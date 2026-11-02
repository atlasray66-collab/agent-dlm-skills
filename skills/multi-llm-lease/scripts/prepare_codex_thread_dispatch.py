#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
import sys

from work_item_lease_lib import claim_next, load_runtime_config, resolve_worker_id


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Claim a work item and generate a ready-to-use Codex new-thread dispatch bundle (with task banner, Gemini 4 tier routing, and dlm-reflect -> dlm-sediment closeout)."
    )
    parser.add_argument("--config", required=True, help="Path to work_item_runtime.json")
    parser.add_argument("--worker", default=None, help="Explicit worker id; defaults to codex-thread-<item_id> or configured worker_env_var")
    parser.add_argument("--worker-env-var", default=None, help="Override configured worker_env_var")
    parser.add_argument("--item-id", default=None, help="Optional explicit work item id (e.g. S001)")
    parser.add_argument("--lease-seconds", type=int, default=None, help="Override lease duration in seconds")
    parser.add_argument("--context-file", action="append", default=None, help="Additional context file paths to inject into the new-thread prompt")
    parser.add_argument("--write-scope", default=None, help="Allowed write scope for the claimed sub-task")
    parser.add_argument("--evidence-path", default=None, help="Target evidence output path for dlm-reflect / dlm-sediment")
    return parser.parse_args()


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    try:
        args = parse_args()
        config = load_runtime_config(args.config, lease_seconds_override=args.lease_seconds)
        default_worker = f"codex-thread-{args.item_id}" if args.item_id else "codex-thread-dispatcher"
        worker = resolve_worker_id(
            args.worker,
            env_var=args.worker_env_var if args.worker_env_var is not None else config.worker_env_var,
            default=default_worker,
        )
        result = claim_next(config, worker, item_id=args.item_id)
        dispatch = dict(result.get("new_thread_dispatch") or {})
        extra_lines: list[str] = []
        if args.context_file:
            extra_lines.append("【必读上下文文件】")
            for ctx in args.context_file:
                extra_lines.append(f"- `{ctx}`")
        if args.write_scope:
            extra_lines.append(f"【允许写入范围】`{args.write_scope}`")
        if args.evidence_path:
            extra_lines.append(f"【验证证据落盘路径】`{args.evidence_path}`")
        if extra_lines:
            dispatch["starter_prompt"] = dispatch.get("starter_prompt", "") + "\n\n" + "\n".join(extra_lines)
        result["new_thread_dispatch"] = dispatch
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc), "type": type(exc).__name__}, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
