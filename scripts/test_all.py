#!/usr/bin/env python3
"""Run all bundled unit and integration suites in an isolated temporary host."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SUITES = (
    "skills/_shared/scripts",
    "skills/multi-llm-lease/tests",
    "skills/multi-llm-lease/scripts",
    "skills/dlm-version-master/scripts",
)


def main() -> int:
    failed = []
    with tempfile.TemporaryDirectory(prefix="dlm-pack-test-") as temporary:
        host = Path(temporary)
        (host / "docs-llm").mkdir()
        env = dict(os.environ)
        for name in ("DLM_PROJECT_ROOT", "DLM_DOC_LLM_DIR", "DLM_SKILL_ENTRYPOINT", "PYTHONPATH"):
            env.pop(name, None)
        env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        for suite in SUITES:
            print(f"\n=== {suite} ===", flush=True)
            result = subprocess.run(
                [sys.executable, "-B", "-X", "utf8", "-m", "unittest", "discover", "-s", str(ROOT / suite), "-p", "test_*.py"],
                cwd=host,
                env=env,
            )
            if result.returncode:
                failed.append(suite)

        # Also test install.py --skills-dir and --check
        install_target = host / "installed-skills"
        r_inst = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / "install.py"), "--skills-dir", str(install_target)], env=env)
        r_chk = subprocess.run([sys.executable, "-B", "-X", "utf8", str(ROOT / "install.py"), "--skills-dir", str(install_target), "--check"], env=env)
        if r_inst.returncode or r_chk.returncode:
            failed.append("install.py")

    for pc in ROOT.rglob("__pycache__"):
        shutil.rmtree(pc, ignore_errors=True)
    print("\n[FAIL] " + ", ".join(failed) if failed else "\n[OK] All suites passed")
    return int(bool(failed))


if __name__ == "__main__":
    raise SystemExit(main())
