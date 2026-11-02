#!/usr/bin/env python3
"""Compatibility wrapper for the shared DLM doctor."""

from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True


def main() -> None:
    shared = Path(__file__).resolve().parents[2] / "_shared" / "scripts" / "dlm_doctor.py"
    if not shared.is_file():
        print(f"[ERROR] Shared script not found: {shared}")
        raise SystemExit(1)
    runpy.run_path(str(shared), run_name="__main__")


if __name__ == "__main__":
    main()
