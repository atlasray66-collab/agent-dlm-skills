#!/usr/bin/env python3
"""Regression tests for the claim/lease runtime (run: python -B -X utf8 -m unittest discover -s tests)."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import work_item_lease_lib as lib  # noqa: E402

TABLE = """# Work items

| 编号 | 标题 | 状态 | 执行者 | 开始时间 | 完成时间 | 运行备注 |
|---|---|---|---|---|---|---|
| W001 | first | ⬜ | — | — | — | — |
| W002 | second | ⬜ | — | — | — | — |
| W003 | third \\| piped | ⬜ | — | — | — | — |
"""


class LeaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        (root / "work_items.md").write_bytes(("﻿" + TABLE).replace("\n", "\r\n").encode("utf-8"))
        self.config_path = root / "work_item_runtime.json"
        self.config_path.write_text(
            json.dumps(
                {
                    "epic_id": "E000",
                    "label": "test",
                    "path_base": "config_dir",
                    "work_items_path": "work_items.md",
                    "claims_dir": "out/claims",
                    "worker_env_var": None,
                }
            ),
            encoding="utf-8",
        )
        self.config = lib.load_runtime_config(str(self.config_path))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def table(self) -> lib.MarkdownTable:
        return lib.load_markdown_table(self.config.work_items_path, self.config.columns)

    def test_reentry_returns_same_item(self) -> None:
        first = lib.claim_next(self.config, "w1")
        again = lib.claim_next(self.config, "w1")
        self.assertEqual(first["work_item_id"], again["work_item_id"])
        self.assertEqual(again["mode"], "reentered")
        self.assertTrue(again["claim_verified"])

    def test_pipe_in_note_keeps_table_shape_and_encoding(self) -> None:
        lib.claim_next(self.config, "w1", item_id="W001")
        lib.complete_claim(self.config, "w1", "blocked", item_id="W001", note="a|b\nsecond line")
        table = self.table()
        row = table.get_row("W001")
        self.assertEqual(len(row), len(table.headers))
        self.assertEqual(lib.get_row_value(table, row, "运行备注"), "a\\|b second line")
        self.assertTrue(table.has_utf8_bom)
        self.assertEqual(table.newline, "\r\n")
        # pre-escaped pipe in another row survives the rewrite unchanged
        self.assertEqual(lib.get_row_value(table, table.get_row("W003"), "标题"), "third \\| piped")

    def test_unsafe_item_id_rejected(self) -> None:
        with self.assertRaises(ValueError):
            lib.claim_file_path(self.config, "../escape")

    def test_explicit_item_errors_are_specific(self) -> None:
        lib.claim_next(self.config, "w1", item_id="W002")
        with self.assertRaisesRegex(ValueError, "already claimed"):
            lib.claim_next(self.config, "w2", item_id="W002")
        with self.assertRaisesRegex(ValueError, "not in"):
            lib.claim_next(self.config, "w2", item_id="W999")

    def test_concurrent_claims_never_collide(self) -> None:
        results: list[str] = []
        errors: list[str] = []

        def worker(name: str) -> None:
            try:
                results.append(lib.claim_next(self.config, name)["work_item_id"])
            except ValueError as error:
                errors.append(str(error))

        threads = [threading.Thread(target=worker, args=(f"w{i}",)) for i in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(len(results), 3)
        self.assertEqual(len(set(results)), 3)
        self.assertEqual(len(errors), 3)

    def test_heartbeat_extends_lease(self) -> None:
        lib.claim_next(self.config, "w1")
        before = json.loads(next(self.config.claims_dir.glob("*.json")).read_text(encoding="utf-8"))
        result = lib.heartbeat_claim(self.config, "w1", lease_seconds_override=99999)
        after = json.loads(next(self.config.claims_dir.glob("*.json")).read_text(encoding="utf-8"))
        self.assertTrue(result["claim_verified"])
        self.assertGreater(after["expires_at"], before["expires_at"])
        self.assertFalse(self.config.write_lock_path.exists())

    def test_cli_failure_is_json_on_stderr(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-B", "-X", "utf8", str(SCRIPTS / "heartbeat_work_item.py"), "--config", str(self.config_path), "--worker", "nobody"],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stderr.strip().splitlines()[-1])
        self.assertFalse(payload["ok"])



    def test_task_banner_progress_gemini4_and_reflect_sediment_dispatch(self) -> None:
        rows = []
        for idx in range(1, 59):
            item_id = f"S{idx:03d}"
            title = "3D平面拟合导入" if idx == 1 else f"算子迁移任务_{idx:03d}"
            tier = "D2" if idx == 1 else "D1"
            state = "✅" if idx in (2, 3) else "⬜"
            rows.append(f"| {item_id} | {title} | {tier} | {state} | — | — | — | — |")

        table_md = (
            "# Work Items\n\n"
            "| 编号 | 任务 | 分级 | 状态 | 执行者 | 开始时间 | 完成时间 | 运行备注 |\n"
            "| --- | --- | --- | --- | --- | --- | --- | --- |\n"
            + "\n".join(rows)
            + "\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work_items.md").write_text(table_md, encoding="utf-8")
            config_path = root / "work_item_runtime.json"
            config_path.write_text(
                json.dumps(
                    {
                        "epic_id": "E001",
                        "label": "3D算子导入",
                        "path_base": "config_dir",
                        "work_items_path": "work_items.md",
                        "claims_dir": "out/claims",
                        "worker_env_var": None,
                    }
                ),
                encoding="utf-8",
            )
            cfg = lib.load_runtime_config(str(config_path))

            claimed = lib.claim_next(cfg, "thread-s001", item_id="S001")
            self.assertEqual(claimed["task_banner"], "S001 1/58 3D平面拟合导入")
            self.assertEqual(claimed["progress"]["total_count"], 58)
            self.assertEqual(claimed["progress"]["item_index"], 1)
            self.assertEqual(claimed["progress"]["completed_count"], 2)
            self.assertEqual(claimed["progress"]["active_count"], 1)
            self.assertEqual(claimed["progress"]["open_count"], 55)
            self.assertEqual(claimed["gemini4_routing"]["tier"], "D2")
            self.assertEqual(claimed["gemini4_routing"]["model"], "gemini-4-thinking")

            dispatch = claimed["new_thread_dispatch"]
            self.assertEqual(dispatch["thread_title"], "S001 1/58 3D平面拟合导入")
            self.assertTrue(dispatch["prefer_codex_new_thread"])
            self.assertIn("$dlm-reflect", dispatch["starter_prompt"])
            self.assertIn("$dlm-sediment", dispatch["starter_prompt"])
            self.assertIn("S001 1/58 3D平面拟合导入", dispatch["starter_prompt"])


if __name__ == "__main__":
    unittest.main()
