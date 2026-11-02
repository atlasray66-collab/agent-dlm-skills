"""Focused, isolated regressions for advisory impact analysis (standard library only)."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import dlm_impact as impact


HERE = Path(__file__).resolve().parent
WRAPPER = HERE.parents[1] / "dlm-load" / "scripts" / "dlm_impact.py"


class ImpactTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.a = "doc_llm/Domains/main/L2_Modules/a.md"
        self.b = "doc_llm/Domains/other/L2_Modules/b.md"
        self.c = "doc_llm/Domains/other/L2_Modules/c.md"
        self.write(self.a, '---\nmatch_globs: ["src/**/*.cs"]\n---\n# A\n')

    def write(self, rel, content):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8", newline="")
        return path

    def module(self, rel, deps, pattern="other/*.cs"):
        self.write(rel, f'---\nmatch_globs:\n  - "{pattern}"\ndepends_on: {json.dumps(deps)}\n---\n# Module\n')

    def run_tool(self, *args, wrapper=False):
        return subprocess.run([sys.executable, "-B", "-X", "utf8", str(WRAPPER if wrapper else HERE / "dlm_impact.py"),
                               "--repo-root", str(self.root), *args], text=True, encoding="utf-8", capture_output=True)

    def test_segment_glob_semantics(self):
        cases = [
            ("src/A.cs", "src/*.cs", True),
            ("src/deep/A.cs", "src/*.cs", False),
            ("src/A.cs", "src/**/*.cs", True),
            ("src/deep/more/A.cs", "src/**/*.cs", True),
            ("src/deep/A.CS", "src/**/*.cs", False),
            ("src/A.cs", "**/A.?s", True),
            ("A.cs", "**/A.cs", True),
            ("src/a.cs", "src/[ab].cs", True),
            ("else/A.cs", "src/**/*.cs", False),
        ]
        for path, pattern, expected in cases:
            with self.subTest(path=path, pattern=pattern):
                self.assertEqual(expected, impact.glob_matches(path, pattern))

    def test_deleted_source_and_old_metadata_are_supported(self):
        result = impact.analyze(self.root, ["src/deleted.cs", "src/deleted.cs"])
        self.assertFalse((self.root / "src/deleted.cs").exists())
        self.assertEqual(["src/deleted.cs"], result["changed_files"])
        self.assertEqual([self.a], [c["path"] for c in result["candidates"]])
        self.assertEqual([], result["warnings"])
        self.assertEqual([], result["unmapped"])
        self.assertTrue(result["advisory"] and result["does_not_change_acceptance"])

    def test_transitive_dependencies_and_cycles_terminate_with_reasons(self):
        self.module(self.b, [self.a, self.c])
        self.module(self.c, [self.b])
        result = impact.analyze(self.root, ["src/x.cs"])
        candidates = {c["path"]: c["reasons"] for c in result["candidates"]}
        self.assertEqual({self.a, self.b, self.c}, set(candidates))
        self.assertIn({"kind": "depends_on", "dependency": self.a}, candidates[self.b])
        self.assertIn({"kind": "depends_on", "dependency": self.c}, candidates[self.b])
        self.assertEqual([{"kind": "depends_on", "dependency": self.b}], candidates[self.c])

    def test_changed_l2_is_direct_and_block_dependencies_propagate(self):
        self.write(self.b, f'---\nmatch_globs: ["ui/*"]\ndepends_on:\n  - "{self.a}"\n---\n# B\n')
        result = impact.analyze(self.root, [self.a])
        self.assertEqual(2, len(result["candidates"]))
        self.assertEqual({"kind": "changed_l2", "changed_file": self.a}, result["candidates"][0]["reasons"][0])

    def test_unknown_dependency_and_unmapped_are_explicit(self):
        missing = "doc_llm/Domains/main/L2_Modules/deleted.md"
        self.module(self.b, [missing, "src/readme.md"])
        result = impact.analyze(self.root, ["unowned/file.txt"])
        self.assertEqual([], result["candidates"])
        self.assertEqual(["unowned/file.txt"], result["unmapped"])
        self.assertEqual(2, len(result["warnings"]))
        self.assertTrue(all("Unknown L2 dependency" in w and "incomplete" in w for w in result["warnings"]))

    def test_explicit_deleted_l2_seeds_surviving_consumers(self):
        (self.root / self.a).unlink()
        self.module(self.b, [self.a])
        self.module(self.c, [self.b])
        result = impact.analyze(self.root, [self.a])
        candidates = {c["path"]: c["reasons"] for c in result["candidates"]}
        self.assertEqual({self.b, self.c}, set(candidates))
        self.assertEqual([{"kind": "changed_missing_dependency", "changed_file": self.a}], candidates[self.b])
        self.assertEqual([{"kind": "depends_on", "dependency": self.b}], candidates[self.c])
        self.assertEqual([], result["unmapped"])
        self.assertTrue(any("Unknown L2 dependency" in w and self.a in w for w in result["warnings"]))
        self.assertFalse((self.root / self.a).exists())

    def test_deleted_dependency_outside_selected_l2_layout_does_not_propagate(self):
        wrong_layout = "doc_llm/Tasks/deleted.md"
        other_project = "other/doc_llm/Domains/main/L2_Modules/deleted.md"
        self.module(self.b, [wrong_layout, other_project])
        result = impact.analyze(self.root, [wrong_layout, other_project])
        self.assertEqual([], result["candidates"])
        self.assertEqual(sorted([wrong_layout, other_project]), result["unmapped"])

    def test_malformed_list_metadata_is_not_silently_empty(self):
        self.write(self.a, '---\nmatch_globs: src/*.cs\ndepends_on: wrong.md\n---\n')
        result = impact.analyze(self.root, ["src/a.cs"])
        self.assertTrue(any("Invalid match_globs list" in w for w in result["warnings"]))
        self.assertTrue(any("Invalid depends_on list" in w for w in result["warnings"]))

    def test_invalid_changed_paths_fail(self):
        for path in ["../secret", "src/../secret", "/secret", "C:/secret", "C:secret", "//host/share/file",
                     "\\\\host\\share\\file", "src/*.cs", ".codex/skills/a.md", "src//file", "src/./file"]:
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    impact.analyze(self.root, [path])

    def test_dangerous_globs_and_dependencies_warn_without_following(self):
        bad = ["../outside/*", "/outside/*", "D:/outside/*", "//host/share/*", ".codex/skills/*", "src/**x"]
        self.write(self.a, f"---\nmatch_globs: {json.dumps(bad)}\ndepends_on: {json.dumps(bad[:-1])}\n---\n")
        result = impact.analyze(self.root, ["src/x.cs"])
        self.assertEqual([], result["candidates"])
        self.assertEqual(len(bad) + len(bad[:-1]), len(result["warnings"]))

    def test_custom_root_explicit_and_contract_redirect(self):
        custom = "knowledge/Domains/custom/L2_Modules/custom.md"
        self.write(custom, '---\nmatch_globs: ["custom/*.cs"]\n---\n')
        result = impact.analyze(self.root, ["custom/a.cs"], "knowledge")
        self.assertEqual([custom], [c["path"] for c in result["candidates"]])
        self.write("doc_llm/dlm.json", json.dumps({"repository_root": ".", "doc_llm_root": "knowledge"}))
        self.assertEqual("knowledge", impact.analyze(self.root, ["custom/a.cs"])["doc_llm_root"])
        self.write("knowledge/dlm.json", json.dumps({"doc_llm_root": "different"}))
        with self.assertRaisesRegex(ValueError, "disagrees"):
            impact.analyze(self.root, ["custom/a.cs"], "knowledge")

    def test_unsafe_custom_roots_and_contract_roots_fail(self):
        for bad in ["../other", "/other", "C:/other", ".codex/skills"]:
            with self.subTest(root=bad):
                with self.assertRaises(ValueError):
                    impact.analyze(self.root, ["src/a.cs"], bad)
                self.write("doc_llm/dlm.json", json.dumps({"doc_llm_root": bad}))
                with self.assertRaises(ValueError):
                    impact.analyze(self.root, ["src/a.cs"])

    def test_no_modules_is_not_no_impact(self):
        (self.root / "empty-doc").mkdir()
        report = impact.analyze(self.root, ["src/a.cs"], "empty-doc")
        self.assertEqual([], report["candidates"])
        self.assertTrue(any("not proof" in warning for warning in report["warnings"]))

    def test_read_only_and_wrapper_json_file(self):
        self.module(self.b, [self.a])
        self.write("changed.json", '\ufeff["src/deleted.cs", "unmapped/中文.txt"]')
        before = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        result = self.run_tool("--changed-files-json", "changed.json", "--json", wrapper=True)
        self.assertEqual(0, result.returncode, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(2, len(report["candidates"]))
        self.assertEqual(["unmapped/中文.txt"], report["unmapped"])
        after = {p.relative_to(self.root).as_posix(): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_wrapper_readable_and_error_exits(self):
        readable = self.run_tool("--changed-file", "src/a.cs", wrapper=True)
        self.assertEqual(0, readable.returncode, readable.stderr)
        self.assertIn("Advisory", readable.stdout)
        for args in [[], ["--changed-file", "../bad"], ["--changed-files-json", "missing.json"]]:
            with self.subTest(args=args):
                result = self.run_tool(*args, "--json", wrapper=True)
                self.assertEqual(2, result.returncode)
                self.assertIn("error", json.loads(result.stdout))
        self.write("changed.json", '["src/a.cs", 4]')
        result = self.run_tool("--changed-files-json", "changed.json", "--json")
        self.assertEqual(2, result.returncode)
        self.assertIn("array of strings", json.loads(result.stdout)["error"])

    def test_symlink_escape_is_rejected_before_read(self):
        def directory_link(link, target):
            link.parent.mkdir(parents=True, exist_ok=True)
            try:
                link.symlink_to(target, target_is_directory=True)
            except OSError as exc:
                if os.name != "nt":
                    self.skipTest(f"Host does not permit symlinks: {exc}")
                # Windows junctions exercise resolve containment without admin symlink privileges.
                result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True)
                if result.returncode:
                    self.skipTest(f"Host does not permit symlinks or directory junctions: {exc}")

        with tempfile.TemporaryDirectory() as outside:
            external = Path(outside)
            (external / "secret.md").write_text("DO NOT READ", encoding="utf-8")
            link = self.root / "escape"
            directory_link(link, external)
            with self.assertRaises(ValueError):
                impact.analyze(self.root, ["escape/deleted.cs"])
            with self.assertRaises(ValueError):
                impact.analyze(self.root, ["src/a.cs"], "escape")
            l2_link = self.root / "doc_llm/Domains/external/L2_Modules"
            directory_link(l2_link, external)
            self.write(self.a, '---\nmatch_globs: ["escape/*.cs"]\n---\n')
            result = impact.analyze(self.root, ["src/a.cs"])
            self.assertTrue(any("Skipped escaping L2" in w for w in result["warnings"]))
            self.assertTrue(any("Glob prefix resolves outside" in w for w in result["warnings"]))
            self.assertFalse(any("DO NOT READ" in w for w in result["warnings"]))


if __name__ == "__main__":
    unittest.main()
