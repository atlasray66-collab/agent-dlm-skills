#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Synchronize independent Codex threads spawned via `codex.exe exec` so that they
are immediately visible in the Codex Desktop project sidebar.
"""

import argparse
import ctypes
import glob
import json
import pathlib
import re
import sqlite3
import struct
import time
import uuid


def detect_allowed_sidebar_source() -> str:
    candidates = glob.glob(
        r"C:\Program Files\WindowsApps\OpenAI.Codex_*\app\resources\app.asar"
    )
    for asar_path in sorted(candidates, reverse=True):
        try:
            raw = pathlib.Path(asar_path).read_bytes()
            m = re.search(rb"var\s+c6\s*=\s*\[([^\]]+)\]", raw)
            if m:
                items = [
                    s.strip().strip(b"\"'").decode("utf-8", errors="ignore")
                    for s in m.group(1).split(b",")
                ]
                if "vscode" in items:
                    return "vscode"
                if "cli" in items:
                    return "cli"
        except Exception:
            pass
    return "vscode"


def send_ipc_broadcast(thread_ids: list[str], retries: int = 3, delay_sec: float = 0.5) -> bool:
    pipe_name = r"\\.\pipe\codex-ipc"
    kernel32 = ctypes.windll.kernel32
    GENERIC_READ = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3

    def write_frame(handle, obj):
        raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        frame = struct.pack("<I", len(raw)) + raw
        written = ctypes.c_ulong(0)
        kernel32.WriteFile(handle, frame, len(frame), ctypes.byref(written), None)

    for attempt in range(max(1, retries)):
        h = kernel32.CreateFileW(
            pipe_name, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None
        )
        if h not in (-1, 0xFFFFFFFF, 0xFFFFFFFFFFFFFFFF):
            try:
                init_id = str(uuid.uuid4())
                write_frame(
                    h,
                    {
                        "type": "request",
                        "requestId": init_id,
                        "method": "initialize",
                        "params": {"clientType": "cli-sidebar-sync"},
                    },
                )
                time.sleep(0.12)
                avail = ctypes.c_ulong(0)
                if kernel32.PeekNamedPipe(h, None, 0, None, ctypes.byref(avail), None) and avail.value > 0:
                    buf = ctypes.create_string_buffer(avail.value)
                    read = ctypes.c_ulong(0)
                    kernel32.ReadFile(h, buf, avail.value, ctypes.byref(read), None)
                for tid in thread_ids:
                    write_frame(
                        h,
                        {
                            "type": "broadcast",
                            "method": "thread-Notification",
                            "sourceClientId": "cli-sidebar-sync",
                            "version": 1,
                            "params": {
                                "method": "thread-started",
                                "params": {"threadId": tid},
                            },
                        },
                    )
                time.sleep(0.1)
                return True
            finally:
                kernel32.CloseHandle(h)
        if attempt + 1 < retries:
            time.sleep(delay_sec)
    return False


def sync_threads(cwd: str | None, thread_ids: list[str] | None, retries: int = 3) -> dict:
    codex_dir = pathlib.Path.home() / ".codex"
    db_path = codex_dir / "state_5.sqlite"
    global_state_path = codex_dir / ".codex-global-state.json"
    allowed_source = detect_allowed_sidebar_source()

    if not db_path.exists():
        return {"ok": False, "error": f"SQLite database not found: {db_path}"}

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()
    if thread_ids:
        placeholders = ",".join("?" for _ in thread_ids)
        rows = cur.execute(
            f"SELECT id, rollout_path, source, archived, title, cwd FROM threads WHERE id IN ({placeholders})",
            thread_ids,
        ).fetchall()
    elif cwd:
        rows = cur.execute(
            "SELECT id, rollout_path, source, archived, title, cwd FROM threads WHERE LOWER(cwd) = LOWER(?) ORDER BY updated_at DESC LIMIT 20",
            (cwd,),
        ).fetchall()
    else:
        rows = cur.execute(
            "SELECT id, rollout_path, source, archived, title, cwd FROM threads WHERE source = 'exec' ORDER BY updated_at DESC LIMIT 20"
        ).fetchall()

    synced_ids = []
    rollout_updated = 0
    for tid, rpath, src, archived, title, row_cwd in rows:
        synced_ids.append(tid)
        p = pathlib.Path(rpath) if rpath else None
        if p and p.exists():
            lines = p.read_text(encoding="utf-8").splitlines()
            if lines:
                first = json.loads(lines[0])
                payload = first.get("payload", {})
                if payload.get("source") != allowed_source:
                    payload["source"] = allowed_source
                    first["payload"] = payload
                    lines[0] = json.dumps(first, ensure_ascii=False)
                    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
                    rollout_updated += 1
        cur.execute(
            "UPDATE threads SET source = ?, archived = 0, archived_at = NULL WHERE id = ?",
            (allowed_source, tid),
        )
    conn.commit()
    conn.close()

    if global_state_path.exists() and synced_ids:
        try:
            gs = json.loads(global_state_path.read_text(encoding="utf-8"))
            changed = False
            for key in ("recently-archived-thread-ids", "archived-thread-ids"):
                if isinstance(gs.get(key), list):
                    before = len(gs[key])
                    gs[key] = [x for x in gs[key] if x not in synced_ids]
                    if len(gs[key]) != before:
                        changed = True
            if changed:
                global_state_path.write_text(json.dumps(gs, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    ipc_ok = send_ipc_broadcast(synced_ids, retries=retries) if synced_ids else True
    return {
        "ok": True,
        "allowedSidebarSource": allowed_source,
        "syncedThreadIds": synced_ids,
        "rolloutFilesUpdated": rollout_updated,
        "ipcBroadcastDelivered": ipc_ok,
    }


def main():
    parser = argparse.ArgumentParser(description="Sync Codex CLI threads into Codex Desktop sidebar.")
    parser.add_argument("--cwd", default=None, help="Filter threads by workspace cwd")
    parser.add_argument("--thread-id", action="append", dest="thread_ids", help="Specific thread ID(s) to sync")
    parser.add_argument("--retry-ipc", type=int, default=3, help="IPC pipe broadcast retry count")
    args = parser.parse_args()
    result = sync_threads(args.cwd, args.thread_ids, retries=args.retry_ipc)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
