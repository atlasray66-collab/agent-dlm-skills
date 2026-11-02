#!/usr/bin/env python3
"""Compatibility entry point for the shared read-only DLM impact advisor."""

from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True


def main() -> None:
    shared = Path(__file__).resolve().parents[2] / "_shared" / "scripts" / "dlm_impact.py"
    if not shared.is_file():
        print(f"[ERROR] Shared script not found: {shared}", file=sys.stderr)
        raise SystemExit(2)
    sys.path.insert(0, str(shared.parent))
    runpy.run_path(str(shared), run_name="__main__")


if __name__ == "__main__":
    main()
