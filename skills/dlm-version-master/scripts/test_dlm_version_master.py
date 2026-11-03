#!/usr/bin/env python3
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import dlm_version_master as vm


class TestDlmVersionMaster(unittest.TestCase):
    def test_build_manifest_and_binary_archive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source_repo"
            archive = Path(tmp) / "binary_archive_repo"
            (root / "bin").mkdir(parents=True, exist_ok=True)
            dll = root / "bin" / "Demo.Core.dll"
            dll.write_bytes(b"MZ-demo-binary-payload")
            versions = {
                "schema": 1,
                "modules": {
                    "Demo.Core": {
                        "project": "src/Demo.Core/Demo.Core.csproj",
                        "output": "bin/Demo.Core.dll",
                        "version": "1.3.0",
                        "sourceHash": "002a1b2c3d4e5f0c63",
                    },
                    "Demo.Native": {
                        "project": "native/Demo.Native/CMakeLists.txt",
                        "kind": "native",
                        "version": "3.80.0",
                        "sourceHash": "2ed99887766558c20",
                        "abiVersion": 1,
                    },
                },
            }
            v_path = root / "build" / "versioning" / "versions.json"
            vm.write_json(v_path, versions)
            m_path = root / "build" / "versioning" / "generated" / "build-manifest.json"
            manifest = vm.build_manifest(root, v_path, output_path=m_path, build_id="408...5a54")
            self.assertEqual(manifest["moduleCount"], 2)
            self.assertEqual(manifest["buildId"], "408...5a54")
            mods = {m["module"]: m for m in manifest["modules"]}
            self.assertEqual(mods["Demo.Core"]["sourceRevision"], "002...0c63")
            self.assertEqual(mods["Demo.Native"]["category"], "Native Engine")
            self.assertIn("buildInfoApi=1", mods["Demo.Native"]["compatibilityPolicy"])
            res = vm.sync_binary_archive(root, archive, m_path, v_path, project_name="DemoProject")
            self.assertTrue(res["committed"])
            self.assertTrue((archive / "metadata" / "build-manifest.json").is_file())
            self.assertTrue((archive / "binaries" / "bin" / "Demo.Core.dll").is_file())
            self.assertIn("修改范围：", res["message"])
            self.assertIn("对应版本：", res["message"])
            self.assertIn("怎么改的：", res["message"])
            self.assertIn("为什么改的：", res["message"])


if __name__ == "__main__":
    unittest.main()
