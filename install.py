#!/usr/bin/env python3
"""Portable installer for the DLM Skill Pack (supports project --host or global --skills-dir)."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True

PACK_ROOT = Path(__file__).resolve().parent
SKILLS_SRC = PACK_ROOT / "skills"
SKILL_ITEMS = (
    "_shared",
    "dlm-build",
    "dlm-load",
    "dlm-plan",
    "dlm-reflect",
    "dlm-sediment",
    "dlm-close-release",
    "dlm-version-master",
    "multi-llm-lease",
)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collect_source_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for item in SKILL_ITEMS:
        base = SKILLS_SRC / item
        for path in sorted(base.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and not path.name.endswith(".pyc"):
                rel = path.relative_to(SKILLS_SRC).as_posix()
                files[rel] = path
    return files


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--host", help="Target project repository root (installs into <host>/.agents/skills/)")
    target.add_argument("--skills-dir", help="Target skills directory directly (e.g. ~/.codex/skills/skills)")
    parser.add_argument("--dry-run", action="store_true", help="Preview installation without writing files")
    parser.add_argument("--check", action="store_true", help="Verify installed files match this pack")
    parser.add_argument("--force", action="store_true", help="Overwrite modified target files")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.host:
        host_root = Path(args.host).expanduser().resolve()
        dest_root = host_root / ".agents" / "skills"
    else:
        host_root = None
        dest_root = Path(args.skills_dir).expanduser().resolve()

    src_files = collect_source_files()
    if args.check:
        mismatches = []
        for rel, src in src_files.items():
            dst = dest_root / rel
            if not dst.is_file() or sha256_file(dst) != sha256_file(src):
                mismatches.append(rel)
        if mismatches:
            print(f"[FAIL] {len(mismatches)} file(s) differ or are missing under {dest_root}")
            for rel in mismatches[:20]:
                print(f"  - {rel}")
            return 1
        print(f"[OK] All {len(src_files)} files verified under {dest_root}")
        return 0

    if args.dry_run:
        print(f"[DRY-RUN] Would install {len(src_files)} files into {dest_root}")
        return 0

    dest_root.mkdir(parents=True, exist_ok=True)
    for rel, src in src_files.items():
        dst = dest_root / rel
        if dst.is_file() and not args.force and sha256_file(dst) != sha256_file(src):
            pass
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)

    if host_root is not None:
        cfg_path = host_root / "dlm.config.json"
        if not cfg_path.exists():
            kb_dir = "doc_llm" if (host_root / "doc_llm").is_dir() else "docs-llm"
            cfg = {
                "knowledge_dir": kb_dir,
                "tasks_dir": f"{kb_dir}/Tasks",
                "cache_dir": "out",
                "locale": "zh-CN",
            }
            cfg_path.write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")

    print(f"[OK] Installed {len(src_files)} files into {dest_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
