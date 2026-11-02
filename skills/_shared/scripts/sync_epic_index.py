#!/usr/bin/env python3
"""Rebuild Epic README indexes from Subtask Meta tables."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlm_common import (PreparedWrite, ReadSnapshot, apply_prepared, atomic_write,
                        decode_text, encode_text, parse_task_meta, read_text)


try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


KNOWN_STATUS = ("📋", "🔄", "⛔", "🛑", "✅")


def write_text(path: Path, text: str, has_bom: bool, newline: str) -> None:
    atomic_write(path, encode_text(text, has_bom, newline))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("epic_dir", nargs="?", help="Epic directory, repository-relative or absolute")
    target.add_argument("--all", action="store_true", help="Process all Epics")
    parser.add_argument("--repo-root", default=".", help="Repository root; defaults to cwd")
    parser.add_argument("--doc-llm-root", default="doc_llm", help="Repository-relative doc_llm root")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check freshness without writing")
    return parser.parse_args()


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def parse_meta(filepath: Path, snapshot: ReadSnapshot | None = None) -> dict[str, str]:
    result = parse_task_meta(read_text(filepath, snapshot)[0], filepath.stem)
    return {key: value or "—" for key, value in result.items()}


def sort_key(path: Path) -> tuple[int, str]:
    match = re.match(r"S(\d+)([a-z]?)", path.stem)
    return (int(match.group(1)), match.group(2)) if match else (10**9, path.name)


def subtask_id(path: Path) -> str:
    match = re.match(r"(S\d+[a-z]?)", path.stem)
    return match.group(1) if match else path.stem


def generate_table(epic_dir: Path, allowed: list[str] | None = None, snapshot: ReadSnapshot | None = None) -> tuple[str, list[str]]:
    files = sorted(snapshot.members(epic_dir / "subtasks", "S*.md") if snapshot else (epic_dir / "subtasks").glob("S*.md"), key=sort_key)
    if not files:
        return "> [WARN] No subtask files found\n", ["No subtask files found"]

    allowed = allowed or ["📋 待办", "🔄 进行中", "⛔ 阻塞", "🛑 已取消", "✅ 完成"]
    counts = {status: 0 for status in allowed}
    rows: list[str] = []
    errors: list[str] = []
    for file in files:
        meta = parse_meta(file, snapshot)
        matched = meta["status"] if meta["status"] in counts else None
        if matched:
            counts[matched] += 1
        else:
            errors.append(f"{file.name}: unknown status '{meta['status']}'")
        sid = subtask_id(file)
        rows.append(
            f"| {sid} | {meta['title']} | {meta['priority']} | {meta['status']} | "
            f"{meta['depends']} | [{sid}](subtasks/{file.name}) |"
        )

    progress = " / ".join(f"{icon} {counts[icon]}" for icon in counts if counts[icon]) or "—"
    header = (
        f"> 本表由 `sync_epic_index.py` 从 Subtask Meta 自动生成（{progress}，共 {len(files)} 项）。\n"
        "> Subtask Meta 是状态唯一事实来源。\n\n"
        "| ID | 子任务 | 优先级 | 状态 | 依赖 | 文件 |\n"
        "|:---:|------|:---:|:---:|:---:|------|\n"
    )
    return header + "\n".join(rows) + "\n", errors


def prepare_readme(epic_dir: Path, table: str, snapshot: ReadSnapshot) -> PreparedWrite | None:
    readme = epic_dir / "README.md"
    if not readme.is_file():
        print(f"[ERROR] Missing README: {readme}")
        return None
    content, has_bom, newline = read_text(readme, snapshot)
    match = re.search(r"(##\s*子任务索引[ \t]*\n)(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
    if not match:
        print(f"[ERROR] Missing '## 子任务索引': {readme}")
        return None
    replacement = match.group(1) + "\n" + table.rstrip("\r\n") + "\n"
    updated = content[: match.start()] + replacement + content[match.end() :]
    return PreparedWrite(readme, encode_text(updated, has_bom, newline), table, "index")


def update_readme(epic_dir: Path, table: str, preview: bool, validate_only: bool = False, check: bool = False) -> bool:
    snapshot = ReadSnapshot()
    item = prepare_readme(epic_dir, table, snapshot)
    return bool(item) and (True if validate_only and not check else apply_prepared([item], snapshot, preview=preview, check=check))


def process(epic_dir: Path, preview: bool, validate_only: bool = False, check: bool = False, allowed: list[str] | None = None) -> bool:
    snapshot = ReadSnapshot()
    table, errors = generate_table(epic_dir, allowed, snapshot)
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        return False
    item = prepare_readme(epic_dir, table, snapshot)
    return bool(item) and (True if validate_only and not check else apply_prepared([item], snapshot, preview=preview, check=check))


def main() -> int:
    try:
        return run()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1


def run() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    doc_root = (repo_root / args.doc_llm_root).resolve()
    if not is_within(doc_root, repo_root) or not doc_root.is_dir():
        print(f"[ERROR] Invalid doc_llm root: {doc_root}")
        return 1

    snapshot = ReadSnapshot(allowed_root=doc_root)
    contract_file = doc_root / "dlm.json"
    try:
        raw_contract = snapshot.optional(contract_file)
        contract = json.loads(decode_text(raw_contract)[0]) if raw_contract is not None else {}
        allowed = contract.get("task_status", {}).get("allowed")
        if allowed is not None and (not isinstance(allowed, list) or not allowed or not all(isinstance(v, str) for v in allowed)):
            raise ValueError("task_status.allowed must be a nonempty string list")
    except (OSError, ValueError) as exc:
        print(f"[ERROR] Invalid contract: {exc}")
        return 1

    if args.all:
        epics = sorted(
            path for path in snapshot.members(doc_root / "Tasks", "E*_*", "dir")
            if snapshot.members(path, "subtasks", "dir")
        )
    else:
        target = Path(args.epic_dir)
        epics = [(target if target.is_absolute() else repo_root / target).resolve()]

    if not epics:
        print("[ERROR] No Epic directories found")
        return 1

    ok = True
    prepared = []
    for epic in epics:
        if not is_within(epic, doc_root) or not epic.is_dir():
            print(f"[ERROR] Epic must be inside doc_llm: {epic}")
            ok = False
            continue
        table, errors = generate_table(epic, allowed, snapshot)
        for error in errors:
            print(f"[ERROR] {error}")
        if errors:
            ok = False
            continue
        item = prepare_readme(epic, table, snapshot)
        if item:
            prepared.append(item)
        else:
            ok = False
    if not ok:
        return 1
    return 0 if apply_prepared(prepared, snapshot, preview=args.preview, check=args.check) else 1


if __name__ == "__main__":
    raise SystemExit(main())
