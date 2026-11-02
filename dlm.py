#!/usr/bin/env python3
"""Root CLI entrypoint for the open-source DLM Skill Pack."""

from __future__ import annotations

import os
from pathlib import Path
import runpy
import sys

sys.dont_write_bytecode = True


def _extract_root(argv: list[str]) -> tuple[str | None, list[str]]:
    remaining: list[str] = []
    host_root: str | None = None
    idx = 0
    while idx < len(argv):
        arg = argv[idx]
        if arg == "--root":
            if idx + 1 >= len(argv):
                raise SystemExit("dlm.py: --root requires a path argument")
            host_root = argv[idx + 1]
            idx += 2
            continue
        if arg.startswith("--root="):
            host_root = arg.split("=", 1)[1]
            idx += 1
            continue
        remaining.append(arg)
        idx += 1
    return host_root, remaining


def main() -> None:
    host_root, remaining = _extract_root(sys.argv[1:])
    if host_root:
        resolved = Path(host_root).expanduser().resolve()
        os.environ["DLM_PROJECT_ROOT"] = str(resolved)
        os.chdir(resolved)
    shared = Path(__file__).resolve().parent / "skills" / "_shared" / "scripts" / "dlm.py"
    sys.argv = [str(shared), *remaining]
    runpy.run_path(str(shared), run_name="__main__")


if __name__ == "__main__":
    main()
