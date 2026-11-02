#!/usr/bin/env python3
"""Compatibility wrapper that delegates to the shared sync_epic_index entrypoint."""

from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True


def main() -> None:
    shared = Path(__file__).resolve().parents[2] / "_shared" / "scripts" / "sync_epic_index.py"
    if not shared.exists():
        print(f"[ERROR] Shared script not found: {shared}")
        sys.exit(1)
    runpy.run_path(str(shared), run_name="__main__")


if __name__ == "__main__":
    main()
