#!/usr/bin/env python3
"""Validate a repository-local DLM contract and active context manifests."""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

# Direct scripts, runpy wrappers and importlib callers share this local module.
sys.dont_write_bytecode = True
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from dlm_common import parse_task_meta


try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


STATUS_RE = re.compile(r"(?m)^\|\s*状态\s*\|\s*([^|]+)\|")
LEGACY_STATUS_RE = re.compile(r"(?m)^>\s*\*\*状态\*\*:\s*([^\r\n]+)")
EPIC_RE = re.compile(r"(?:^|/)E(\d+)_")
ATTR_RE = re.compile(r"([A-Za-z_][\w-]*)=\"([^\"]*)\"")
WINDOWS_ROOT_RE = re.compile(r"^[A-Za-z]:[\\/]")


@dataclass
class Report:
    repo_root: str
    contract: str | None = None
    checked_manifests: int = 0
    checked_paths: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def read_utf8(path: Path, report: Report) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        report.error(f"UTF-8 read failed: {path}: {exc}")
        return ""


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return str(path)


def extract_status(content: str) -> str:
    return parse_task_meta(content)["status"]


def epic_number(path: Path, repo_root: Path) -> int:
    match = EPIC_RE.search(relative(path, repo_root))
    return int(match.group(1)) if match else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Repository root; defaults to cwd")
    parser.add_argument("--contract", default="doc_llm/dlm.json", help="Repository-relative contract path")
    parser.add_argument("--require-contract", action="store_true", help="Fail when the contract is absent")
    parser.add_argument("--include-historical", action="store_true", help="Validate completed/cancelled manifests too")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emit machine-readable JSON")
    return parser.parse_args()


def load_contract(repo_root: Path, contract_rel: str, report: Report, required: bool) -> tuple[dict, Path]:
    contract_path = (repo_root / contract_rel).resolve()
    if not is_within(contract_path, repo_root):
        report.error(f"Contract escapes repository: {contract_rel}")
        return {}, contract_path
    report.contract = relative(contract_path, repo_root)
    if not contract_path.is_file():
        message = f"DLM contract not found: {contract_rel}"
        (report.error if required else report.warn)(message)
        return {}, contract_path
    try:
        data = json.loads(read_utf8(contract_path, report))
    except json.JSONDecodeError as exc:
        report.error(f"Invalid JSON contract: {contract_rel}: {exc}")
        return {}, contract_path
    if not isinstance(data, dict):
        report.error(f"Contract root must be an object: {contract_rel}")
        return {}, contract_path
    return data, contract_path


def contract_value(contract: dict, dotted: str, default):
    current = contract
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def validate_contract(contract: dict, repo_root: Path, report: Report) -> tuple[Path, str, int, set[str], set[str]]:
    schema_version = str(contract.get("schema_version", "legacy"))
    project_id = str(contract.get("project_id", "")).strip()
    doc_rel = str(contract.get("doc_llm_root", "doc_llm")).strip().replace("\\", "/")
    enforce_from = int(contract_value(contract, "manifest.enforce_from_epic", 10**9))
    allowed = set(contract_value(contract, "task_status.allowed", ["📋 待办", "🔄 进行中", "✅ 完成"]))
    active = set(contract_value(contract, "task_status.active", ["📋 待办", "🔄 进行中"]))

    if contract:
        if not schema_version.startswith("7."):
            report.warn(f"Contract schema is {schema_version}; DLM 7.x is recommended")
        if not project_id:
            report.error("Contract project_id is empty")
        if contract.get("repository_root", ".") != ".":
            report.error("repository_root must be '.' so the contract remains portable")
        if contract_value(contract, "manifest.path_base", "repository") != "repository":
            report.error("manifest.path_base must be 'repository' in DLM 7")
        if contract_value(contract, "manifest.allow_absolute_paths", False):
            report.error("manifest.allow_absolute_paths must be false")
        if contract_value(contract, "manifest.allow_external_paths", False):
            report.error("manifest.allow_external_paths must be false")

    doc_root = (repo_root / doc_rel).resolve()
    if not is_within(doc_root, repo_root):
        report.error(f"doc_llm_root escapes repository: {doc_rel}")
    if not doc_root.is_dir():
        report.error(f"doc_llm_root does not exist: {doc_rel}")
    return doc_root, project_id, enforce_from, allowed, active


def validate_manifest(
    task_file: Path,
    content: str,
    repo_root: Path,
    doc_root: Path,
    report: Report,
    project_id: str,
    enforce_from: int,
    blocking: bool,
) -> None:
    task_rel = relative(task_file, repo_root)
    is_v2_scope = epic_number(task_file, repo_root) >= enforce_from
    failure = report.error if (blocking or is_v2_scope) else report.warn
    blocks = re.findall(r"<context_manifest\b[^>]*>[\s\S]*?</context_manifest\s*>", content)
    openings = re.findall(r"<context_manifest\b", content)
    if len(blocks) != 1 or len(openings) != 1:
        failure(f"Exactly one complete context_manifest required: {task_rel}")
        return
    try:
        if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", blocks[0], re.IGNORECASE):
            raise ValueError("XML declarations/DTD are not allowed in a manifest")
        manifest = ET.fromstring(blocks[0])
    except (ET.ParseError, ValueError) as exc:
        failure(f"Invalid context_manifest XML: {task_rel}: {exc}")
        return
    report.checked_manifests += 1
    header_attrs = manifest.attrib
    if is_v2_scope:
        if header_attrs.get("schema") != "2":
            report.error(f'Manifest schema="2" required: {task_rel}')
        if project_id and header_attrs.get("project") != project_id:
            report.error(f"Manifest project must be '{project_id}': {task_rel}")
    expected_epic = re.match(r"(E\d+)_", task_file.parent.parent.name)
    expected_task = re.match(r"(S\d+[a-z]?)", task_file.stem)
    for attr, expected in [("epic", expected_epic), ("task", expected_task)]:
        if header_attrs.get(attr) and expected and header_attrs[attr] != expected[1]:
            failure(f"Manifest {attr} conflicts with task identity: {task_rel}")
    tags = list(manifest)
    if not tags:
        failure(f"Manifest has no file entries: {task_rel}")
        return
    if any(tag.tag != "file" or len(tag) for tag in tags):
        failure(f"Manifest children must be file entries: {task_rel}")
        return

    seen: set[str] = set()
    for tag in tags:
        attrs = tag.attrib
        if (is_v2_scope or header_attrs.get("schema") == "2") and not attrs.get("intent", "").strip():
            failure(f"Manifest file missing intent: {task_rel}")
        path_text = attrs.get("path", "").strip()
        required_text = attrs.get("required")
        defer_text = attrs.get("defer", "false")
        if not path_text:
            (report.error if blocking else report.warn)(f"Manifest file missing path: {task_rel}")
            continue
        if required_text not in {"true", "false"}:
            (report.error if blocking else report.warn)(f"Manifest file has invalid required: {task_rel} -> {path_text}")
            continue
        if defer_text not in {"true", "false"}:
            (report.error if blocking else report.warn)(f"Manifest file has invalid defer: {task_rel} -> {path_text}")
            continue
        if defer_text == "true" and required_text != "false":
            report.error(f"defer=true requires required=false: {task_rel} -> {path_text}")

        report.checked_paths += 1
        normalized = path_text.replace("\\", "/")
        if normalized != path_text and is_v2_scope:
            report.error(f"DLM 7 manifest paths must use '/': {task_rel} -> {path_text}")
        if normalized.startswith(("/", "//")) or WINDOWS_ROOT_RE.match(normalized):
            report.error(f"Absolute manifest path is forbidden: {task_rel} -> {path_text}")
            continue
        if any(c in normalized for c in "*?[]"):
            report.error(f"Manifest must reference a concrete file: {task_rel} -> {path_text}")
            continue
        pure = PurePosixPath(normalized)
        if ".." in pure.parts:
            report.error(f"Manifest path traversal is forbidden: {task_rel} -> {path_text}")
            continue
        if normalized in seen:
            report.warn(f"Duplicate manifest path: {task_rel} -> {path_text}")
        seen.add(normalized)

        candidate = (repo_root / Path(*pure.parts)).resolve()
        if not is_within(candidate, repo_root):
            report.error(f"Manifest path escapes repository: {task_rel} -> {path_text}")
            continue
        resolved_candidate = candidate
        if not candidate.exists() and not is_v2_scope:
            legacy_candidate = (doc_root / Path(*pure.parts)).resolve()
            if is_within(legacy_candidate, doc_root):
                resolved_candidate = legacy_candidate
        if resolved_candidate.is_dir():
            message = f"Manifest path must target a file: {task_rel} -> {path_text}"
            (report.error if is_v2_scope else report.warn)(message)
        elif not resolved_candidate.is_file():
            if blocking and required_text == "true" and is_v2_scope:
                report.error(f"Required manifest path missing: {task_rel} -> {path_text}")
            else:
                report.warn(f"Manifest path missing: {task_rel} -> {path_text}")


def run(args: argparse.Namespace) -> Report:
    repo_root = Path(args.repo_root).resolve()
    report = Report(repo_root=str(repo_root))
    if not repo_root.is_dir():
        report.error(f"Repository root does not exist: {repo_root}")
        return report

    contract, _ = load_contract(repo_root, args.contract, report, args.require_contract)
    doc_root, project_id, enforce_from, allowed, active = validate_contract(contract, repo_root, report)

    for rel in ("README.md", "BRIEF.md", "00_Global/L0_global_redlines.md", "Tasks/backlog.md"):
        if not (doc_root / rel).is_file():
            report.error(f"Required DLM entry missing: {relative(doc_root / rel, repo_root)}")

    task_root = doc_root / "Tasks"
    if task_root.is_dir():
        for task_file in sorted(task_root.glob("E*_*/subtasks/S*.md")):
            content = read_utf8(task_file, report)
            status = extract_status(content)
            number = epic_number(task_file, repo_root)
            if not status:
                if number >= enforce_from:
                    report.error(f"Subtask status missing: {relative(task_file, repo_root)}")
                continue
            if allowed and status not in allowed:
                message = f"Unknown subtask status '{status}': {relative(task_file, repo_root)}"
                if number >= enforce_from:
                    report.error(message)
                elif args.include_historical:
                    report.warn(message)
            if status == "⛔ 阻塞" and "## 阻塞说明" not in content:
                message = f"Blocked subtask needs '## 阻塞说明': {relative(task_file, repo_root)}"
                (report.error if number >= enforce_from else report.warn)(message)
            is_active = status in active
            strict_scope = number >= enforce_from
            if is_active or args.include_historical:
                validate_manifest(
                    task_file,
                    content,
                    repo_root,
                    doc_root,
                    report,
                    project_id,
                    enforce_from,
                    is_active and strict_scope,
                )

    return report


def emit(report: Report, json_output: bool) -> None:
    payload = {
        "repo_root": report.repo_root,
        "contract": report.contract,
        "checked_manifests": report.checked_manifests,
        "checked_paths": report.checked_paths,
        "errors": report.errors,
        "warnings": report.warnings,
    }
    if json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(
        "DLM doctor: "
        f"manifests={report.checked_manifests}, paths={report.checked_paths}, "
        f"errors={len(report.errors)}, warnings={len(report.warnings)}"
    )
    for warning in report.warnings:
        print(f"[WARN] {warning}")
    for error in report.errors:
        print(f"[ERROR] {error}")


def main() -> int:
    args = parse_args()
    report = run(args)
    emit(report, args.json_output)
    return 1 if report.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
