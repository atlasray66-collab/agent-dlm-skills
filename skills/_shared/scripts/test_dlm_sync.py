"""Behavior regressions for shared Meta and guarded index writes.

Run with TMP/TEMP/TMPDIR pointing to a workspace scratch directory and -B.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import dlm_common as common
import sync_epic_index as epic
import sync_l1_route as route


class GuardedSyncTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.epic = self.root / "doc_llm/Tasks/E001_example"
        self.domain = self.root / "doc_llm/Domains/one"
        self.source = self.write("doc_llm/Tasks/E001_example/subtasks/S001.md", "# S001: Example\n\n## Meta\n| 状态 | ACTIVE |\n| 优先级 | P1 |\n| 依赖 | 无 |\n")
        self.target = self.write("doc_llm/Tasks/E001_example/README.md", "# Epic\n\n## 子任务索引\n\nold\n\n## History\nkeep\n", bom=True, newline="\r\n")
        self.write("doc_llm/dlm.json", json.dumps({"task_status": {"allowed": ["ACTIVE", "DONE"]}}))
        self.l2 = self.write("doc_llm/Domains/one/L2_Modules/one.md", '---\nstatus: ready\nmatch_globs:\n  - "src/*.py"\ndepends_on: ["doc_llm/Domains/two/L2_Modules/two.md"]\n---\n# One\n')
        self.l1 = self.write("doc_llm/Domains/one/L1_one_router.md", "# Route\n\n## 路由表\n\nold\n", bom=True, newline="\r\n")

    def write(self, relative, text, bom=False, newline="\n"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(common.encode_text(text, bom, newline))
        return path

    def prepare(self, kind="epic"):
        snapshot = common.ReadSnapshot()
        if kind == "epic":
            table, errors = epic.generate_table(self.epic, ["ACTIVE", "DONE"], snapshot)
            item = epic.prepare_readme(self.epic, table, snapshot)
        else:
            table, errors = route.generate_table(self.domain, snapshot)
            item = route.prepare_l1(self.domain, table, snapshot)
        self.assertEqual([], errors)
        self.assertIsNotNone(item)
        return item, snapshot

    def apply(self, item, snapshot, **kwargs):
        with contextlib.redirect_stdout(io.StringIO()):
            return common.apply_prepared([item], snapshot, **kwargs)

    def test_explicit_meta_agrees_across_doctor_and_indexer(self):
        content = "# S001: Heading\n| 状态 | DONE |\n| 优先级 | OLD |\n\n## Meta\n| 状态 | ACTIVE |\n| 优先级 | P1 |\n\n## History\n| 状态 | DONE |\n"
        self.source.write_text(content, encoding="utf-8")
        spec = importlib.util.spec_from_file_location("doctor_sync_test", HERE / "dlm_doctor.py")
        doctor = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = doctor
        spec.loader.exec_module(doctor)
        self.assertEqual("ACTIVE", doctor.extract_status(content))
        self.assertEqual({"title": "Heading", "status": "ACTIVE", "priority": "P1", "depends": "—"}, epic.parse_meta(self.source))

    def test_absent_explicit_fields_do_not_inherit_leading_or_history(self):
        for explicit in ["## Meta\n| 优先级 | P2 |\n", "## Meta"]:
            with self.subTest(explicit=explicit):
                content = "# S001: Heading\n| 状态 | DONE |\n| 依赖 | S099 |\n\n" + explicit
                fields = common.parse_task_meta(content)
                self.assertEqual("", fields["status"])
                self.assertEqual("", fields["depends"])
        self.assertEqual("", common.parse_task_meta("# S001\n\n## History\n| 状态 | DONE |\n")["status"])

    def test_legacy_leading_status_is_preserved(self):
        self.assertEqual("ACTIVE", common.parse_task_meta("# S001\n> **状态**: ACTIVE\n\n## History\n| 状态 | DONE |\n")["status"])

    def test_source_target_addition_and_deletion_reject_without_write(self):
        for kind in ["epic", "route"]:
            source = self.source if kind == "epic" else self.l2
            target = self.target if kind == "epic" else self.l1
            for mutation in ["source", "target", "new", "delete"]:
                with self.subTest(kind=kind, mutation=mutation):
                    original_source, original_target = source.read_bytes(), target.read_bytes()
                    item, snapshot = self.prepare(kind)
                    added = source.parent / ("S002.md" if kind == "epic" else "two.md")
                    if mutation == "source":
                        source.write_bytes(original_source + b"\nchanged")
                    elif mutation == "target":
                        target.write_bytes(original_target + b"\nuser edit")
                    elif mutation == "new":
                        added.write_bytes(original_source)
                    else:
                        source.unlink()
                    before_apply = target.read_bytes()
                    self.assertFalse(self.apply(item, snapshot))
                    self.assertEqual(before_apply, target.read_bytes())
                    source.write_bytes(original_source)
                    target.write_bytes(original_target)
                    added.unlink(missing_ok=True)

    def test_new_route_target_rejects(self):
        item, snapshot = self.prepare("route")
        self.write("doc_llm/Domains/one/L1_second_router.md", "# Other\n")
        self.assertFalse(self.apply(item, snapshot))

    def test_snapshot_reads_once_then_detects_change(self):
        snapshot = common.ReadSnapshot()
        first = snapshot.read(self.source)
        self.source.write_bytes(first + b"\nchanged")
        self.assertEqual(first, snapshot.read(self.source))
        with self.assertRaisesRegex(ValueError, "Input changed"):
            snapshot.validate()

    def test_replace_failure_keeps_original_and_cleans_temp(self):
        item, snapshot = self.prepare()
        original = self.target.read_bytes()
        with patch.object(common.os, "replace", side_effect=PermissionError("injected replace error")):
            self.assertFalse(self.apply(item, snapshot))
        self.assertEqual(original, self.target.read_bytes())
        self.assertEqual([], list(self.target.parent.glob(".dlm-*.tmp")))

    def test_bom_eol_preview_check_and_idempotence(self):
        for kind in ["epic", "route"]:
            with self.subTest(kind=kind):
                item, snapshot = self.prepare(kind)
                before = item.path.read_bytes()
                self.assertTrue(self.apply(item, snapshot, preview=True))
                self.assertEqual(before, item.path.read_bytes())
                self.assertFalse(self.apply(item, snapshot, check=True))
                self.assertEqual(before, item.path.read_bytes())
                self.assertTrue(self.apply(item, snapshot))
                after = item.path.read_bytes()
                self.assertTrue(after.startswith(b"\xef\xbb\xbf"))
                self.assertNotIn(b"\n", after.replace(b"\r\n", b""))
                fresh, fresh_snapshot = self.prepare(kind)
                self.assertTrue(self.apply(fresh, fresh_snapshot, check=True))
                with patch.object(common, "atomic_write", side_effect=AssertionError("idempotent write")):
                    self.assertTrue(self.apply(fresh, fresh_snapshot))
                self.assertEqual(after, item.path.read_bytes())

    def test_frontmatter_lists_and_rejectable_scalars(self):
        self.assertEqual(["doc_llm/Domains/two/L2_Modules/two.md"], route.parse_frontmatter(self.l2)["depends_on"])
        self.l2.write_text('---\nmatch_globs: "src/*.py"\ndepends_on:\n  - "doc_llm/one.md"\n---\n# One\n', encoding="utf-8")
        self.assertEqual(["doc_llm/one.md"], route.parse_frontmatter(self.l2)["depends_on"])
        self.assertIsInstance(route.parse_frontmatter(self.l2)["match_globs"], str)
        self.assertTrue(route.generate_table(self.domain)[1])
        self.l2.write_text('---\nmatch_globs: ["src/*.py"]\ndepends_on: bad-scalar\n---\n# One\n', encoding="utf-8")
        self.assertEqual("bad-scalar", route.parse_frontmatter(self.l2)["depends_on"])

    def test_all_input_validation_precedes_any_write(self):
        self.write("doc_llm/Tasks/E002_bad/subtasks/S001.md", "# S001\n\n## Meta\n| 状态 | INVALID |\n")
        self.write("doc_llm/Tasks/E002_bad/README.md", "# Bad\n\n## 子任务索引\nold\n")
        before = self.target.read_bytes()
        with patch.object(sys, "argv", ["sync", "--repo-root", str(self.root), "--all"]), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, epic.main())
        self.assertEqual(before, self.target.read_bytes())

    def test_main_detects_new_epic_domain_and_contract_changes(self):
        for module, mode in [(epic, "epic"), (route, "domain"), (epic, "contract")]:
            with self.subTest(mode=mode):
                original_apply = common.apply_prepared
                original_target = self.target.read_bytes()
                original_l1 = self.l1.read_bytes()
                added = None
                contract = self.root / "doc_llm/dlm.json"
                original_contract = contract.read_bytes()
                def inject(prepared, snapshot, **kwargs):
                    nonlocal added
                    if mode == "contract":
                        contract.write_bytes(original_contract + b"\n ")
                    else:
                        added = self.root / ("doc_llm/Tasks/E999_new" if mode == "epic" else "doc_llm/Domains/new")
                        added.mkdir()
                    return original_apply(prepared, snapshot, **kwargs)
                with patch.object(module, "apply_prepared", side_effect=inject), patch.object(sys, "argv", ["sync", "--repo-root", str(self.root), "--all"]), contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(1, module.main())
                self.assertEqual(original_target, self.target.read_bytes())
                self.assertEqual(original_l1, self.l1.read_bytes())
                contract.write_bytes(original_contract)
                if added:
                    added.rmdir()

    def test_direct_and_runpy_wrappers_are_compatible(self):
        suite = HERE.parents[1]
        paths = [HERE / "dlm_doctor.py", HERE / "sync_epic_index.py", HERE / "sync_l1_route.py"]
        for skill, script in [("dlm-load", "dlm_doctor.py"), ("dlm-build", "dlm_doctor.py"), ("dlm-build", "sync_l1_route.py"), ("dlm-plan", "sync_epic_index.py"), ("dlm-sediment", "sync_epic_index.py"), ("dlm-sediment", "sync_l1_route.py")]:
            paths.append(suite / skill / "scripts" / script)
        for path in paths:
            with self.subTest(path=path):
                result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(path), "--help"], encoding="utf-8", text=True, capture_output=True)
                self.assertEqual(0, result.returncode, result.stdout + result.stderr)
        for path in [suite / "dlm-plan/scripts/sync_epic_index.py", suite / "dlm-build/scripts/sync_l1_route.py"]:
            result = subprocess.run([sys.executable, "-B", "-X", "utf8", str(path), "--repo-root", str(self.root), "--all", "--preview"], encoding="utf-8", text=True, capture_output=True)
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_all_cli_rejects_resolved_directory_and_target_escapes_before_reads(self):
        """Mock junction/file-link resolution without requiring Windows link privileges."""
        outside = self.write("external/untouched.md", "external sentinel\n")
        original_resolve, original_read = Path.resolve, Path.read_bytes
        for module, target in [(epic, self.epic), (route, self.domain), (epic, self.target), (route, self.l1)]:
            with self.subTest(module=module.__name__, target=target):
                saved = {p: p.read_bytes() for p in [outside, self.target, self.l1]}
                def redirected(path, *args, **kwargs):
                    if path.absolute() == target.absolute():
                        return outside.parent if target.is_dir() else outside
                    return original_resolve(path, *args, **kwargs)
                def guarded_read(path):
                    resolved = redirected(path)
                    if resolved == outside or resolved == outside.parent:
                        raise AssertionError("escaped target was read before containment check")
                    return original_read(path)
                output = io.StringIO()
                with patch.object(Path, "resolve", redirected), patch.object(Path, "read_bytes", guarded_read), patch.object(sys, "argv", ["sync", "--repo-root", str(self.root), "--all"]), contextlib.redirect_stdout(output):
                    self.assertEqual(1, module.main())
                self.assertIn("outside allowed DLM root", output.getvalue())
                for path, contents in saved.items():
                    self.assertEqual(contents, path.read_bytes())

    def test_snapshot_checks_optional_members_and_retargeting_before_read(self):
        allowed = self.root / "doc_llm"
        outside = self.write("external/input.txt", "external sentinel\n")
        snapshot = common.ReadSnapshot(allowed_root=allowed)
        snapshot.read(self.source)
        with self.assertRaisesRegex(ValueError, "outside allowed"):
            snapshot.optional(outside)
        with self.assertRaisesRegex(ValueError, "outside allowed"):
            snapshot.members(outside.parent, "*")
        original_resolve, original_read = Path.resolve, Path.read_bytes
        def redirected(path, *args, **kwargs):
            return outside if path.absolute() == self.source.absolute() else original_resolve(path, *args, **kwargs)
        def guarded_read(path):
            if path.absolute() == self.source.absolute():
                raise AssertionError("retargeted source was read before containment check")
            return original_read(path)
        with patch.object(Path, "resolve", redirected), patch.object(Path, "read_bytes", guarded_read):
            with self.assertRaisesRegex(ValueError, "outside allowed"):
                snapshot.validate()
            with self.assertRaisesRegex(ValueError, "outside allowed"):
                snapshot.read(self.source)

    def test_plain_entrypoints_do_not_create_bytecode_without_B_flag(self):
        isolated = self.root / "isolated-scripts"
        isolated.mkdir()
        for name in ["dlm_common.py", "dlm_doctor.py", "sync_epic_index.py", "sync_l1_route.py"]:
            (isolated / name).write_bytes((HERE / name).read_bytes())
        environment = dict(os.environ)
        environment.pop("PYTHONDONTWRITEBYTECODE", None)
        for name in ["dlm_doctor.py", "sync_epic_index.py", "sync_l1_route.py"]:
            with self.subTest(name=name):
                arguments = ["--help"] if name == "dlm_doctor.py" else ["--repo-root", str(self.root), "--all", "--check"]
                result = subprocess.run([sys.executable, "-X", "utf8", str(isolated / name), *arguments], env=environment, encoding="utf-8", text=True, capture_output=True)
                self.assertEqual(0 if name == "dlm_doctor.py" else 1, result.returncode, result.stdout + result.stderr)
                if name != "dlm_doctor.py":
                    self.assertIn("Stale", result.stdout)
        self.assertFalse((isolated / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
