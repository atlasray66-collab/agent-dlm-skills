#!/usr/bin/env python3
"""Read-only, advisory L2 review candidates for an explicit set of changed paths.

Globs are repository-relative, case-sensitive and slash-separated. *, ? and []
match within one component; a whole ** component matches zero or more components.
No source files, Git state, statuses, acceptance records or databases are changed.
"""

from __future__ import annotations

import argparse
from collections import deque
from fnmatch import fnmatchcase
from functools import lru_cache
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from sync_l1_route import parse_frontmatter


def within(path: Path, root: Path) -> bool:
    return path.is_relative_to(root)


def relative_path(value: str, *, pattern: bool = False) -> str:
    """Validate before normalization so traversal and drive forms cannot disappear."""
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("Expected a nonempty repository-relative path without outer whitespace")
    value = value.replace("\\", "/")
    parts = value.split("/")
    if value.startswith("/") or any(part in ("", ".", "..") for part in parts):
        raise ValueError(f"Absolute, empty or traversal path component: {value}")
    if any(char in value for char in (":", "\x00", "\n", "\r")):
        raise ValueError(f"Drive, stream or control characters in path: {value}")
    if any(parts[i].lower() in (".codex", ".claude", ".agents") and parts[i + 1].lower() == "skills"
           for i in range(len(parts) - 1)):
        raise ValueError(f"Skill roots are not project knowledge paths: {value}")
    if not pattern and any(char in value for char in "*?[]"):
        raise ValueError(f"Expected a concrete path, not a glob: {value}")
    if pattern and any("**" in part and part != "**" for part in parts):
        raise ValueError(f"** must occupy a whole glob component: {value}")
    return value


def safe_path(root: Path, value: str) -> tuple[str, Path]:
    normalized = relative_path(value)
    path = (root / normalized).resolve()
    if not within(path, root):
        raise ValueError(f"Path resolves outside the repository: {normalized}")
    return normalized, path


def safe_glob(root: Path, value: str) -> str:
    normalized = relative_path(value, pattern=True)
    # Validate the concrete prefix without expanding a glob or reading source files.
    prefix = []
    for part in normalized.split("/"):
        if any(char in part for char in "*?["):
            break
        prefix.append(part)
    if prefix and not within((root / "/".join(prefix)).resolve(), root):
        raise ValueError(f"Glob prefix resolves outside the repository: {normalized}")
    return normalized


def glob_matches(path: str, pattern: str) -> bool:
    pieces, globs = path.split("/"), pattern.split("/")

    @lru_cache(maxsize=None)
    def match(i: int, j: int) -> bool:
        if j == len(globs):
            return i == len(pieces)
        if globs[j] == "**":
            return match(i, j + 1) or (i < len(pieces) and match(i + 1, j))
        return i < len(pieces) and fnmatchcase(pieces[i], globs[j]) and match(i + 1, j + 1)

    return match(0, 0)


def load_doc_root(root: Path, requested: str | None) -> tuple[str, Path]:
    doc_rel, doc_root = safe_path(root, requested or "doc_llm")
    contract_path = doc_root / "dlm.json"
    if contract_path.exists():
        if not within(contract_path.resolve(), root):
            raise ValueError("DLM contract resolves outside the repository")
        contract = json.loads(contract_path.read_text(encoding="utf-8-sig"))
        if not isinstance(contract, dict):
            raise ValueError("DLM contract must be a JSON object")
        if contract.get("repository_root", ".") != ".":
            raise ValueError("DLM contract repository_root must be '.'")
        if "doc_llm_root" in contract:
            declared_rel, declared_root = safe_path(root, contract["doc_llm_root"])
            if requested is not None and declared_root != doc_root:
                raise ValueError("--doc-llm-root disagrees with its dlm.json contract")
            doc_rel, doc_root = declared_rel, declared_root
    if not doc_root.is_dir():
        raise ValueError(f"DLM root does not exist: {doc_rel}")
    return doc_rel, doc_root


def analyze(root: Path, changed: list[str], requested_root: str | None = None) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise ValueError("Repository root does not exist")
    # A caller cannot turn a personal skills installation into the project root.
    root_parts = [part.lower() for part in root.parts]
    if any(root_parts[i] in (".codex", ".claude", ".agents") and root_parts[i + 1] == "skills"
           for i in range(len(root_parts) - 1)):
        raise ValueError("Repository root cannot be a skills installation")
    doc_rel, doc_root = load_doc_root(root, requested_root)
    changed_files = sorted({safe_path(root, value)[0] for value in changed})
    warnings: list[str] = []
    modules: dict[str, dict] = {}
    domains = doc_root / "Domains"
    if not within(domains.resolve(), doc_root):
        raise ValueError("Domains root resolves outside the selected DLM root")
    if not domains.is_dir():
        warnings.append(f"No Domains directory: {doc_rel}/Domains; coverage is incomplete")
    # Fixed-depth discovery follows the existing DLM Domains/L2_Modules contract.
    for domain in sorted(domains.iterdir()) if domains.is_dir() else []:
        if not within(domain.resolve(), doc_root):
            warnings.append(f"Skipped escaping Domain: {domain.name}")
            continue
        if not domain.is_dir():
            continue
        l2_root = domain / "L2_Modules"
        if not within(l2_root.resolve(), doc_root):
            warnings.append(f"Skipped escaping L2_Modules: {domain.name}")
            continue
        for path in sorted(l2_root.glob("*.md")):
            rel = path.relative_to(root).as_posix()
            if not within(path.resolve(), doc_root):
                warnings.append(f"Skipped escaping L2 document: {rel}")
                continue
            try:
                meta = parse_frontmatter(path)
                if meta is None:
                    warnings.append(f"Missing front matter: {rel}; mapping coverage is incomplete")
                    meta = {}
                modules[rel] = meta
            except (OSError, UnicodeError, ValueError) as exc:
                warnings.append(f"Cannot parse {rel}: {exc}; mapping coverage is incomplete")
                modules[rel] = {}

    reasons: dict[str, list[dict]] = {}
    dependents: dict[str, list[str]] = {}
    mapped: set[str] = set()

    def add(path: str, reason: dict) -> None:
        entries = reasons.setdefault(path, [])
        if reason not in entries:
            entries.append(reason)

    for path, meta in modules.items():
        if path in changed_files:
            mapped.add(path)
            add(path, {"kind": "changed_l2", "changed_file": path})
        globs = meta.get("match_globs", [])
        if not isinstance(globs, list):
            warnings.append(f"Invalid match_globs list: {path}")
            globs = []
        if not globs:
            warnings.append(f"No match_globs: {path}; source mapping coverage is incomplete")
        for raw_glob in globs:
            try:
                pattern = safe_glob(root, raw_glob)
            except (ValueError, OSError) as exc:
                warnings.append(f"Rejected match_globs in {path}: {exc}")
                continue
            for changed_file in changed_files:
                if glob_matches(changed_file, pattern):
                    mapped.add(changed_file)
                    add(path, {"kind": "match_glob", "changed_file": changed_file, "glob": pattern})
        dependencies = meta.get("depends_on", [])
        if not isinstance(dependencies, list):
            warnings.append(f"Invalid depends_on list: {path}; dependency coverage is incomplete")
            continue
        for dependency in dependencies:
            try:
                dep_rel, dep_path = safe_path(root, dependency)
            except (ValueError, OSError) as exc:
                warnings.append(f"Rejected depends_on in {path}: {exc}; dependency coverage is incomplete")
                continue
            if dep_rel not in modules:
                warnings.append(f"Unknown L2 dependency in {path}: {dep_rel}; dependency coverage is incomplete")
                # An explicitly changed, deleted L2 can still seed its surviving
                # consumers. Its absent content is never read or reconstructed.
                try:
                    l2_parts = Path(dep_rel).relative_to(Path(doc_rel)).parts
                except ValueError:
                    l2_parts = ()
                if (dep_rel in changed_files and not dep_path.exists()
                        and within(dep_path, doc_root)
                        and len(l2_parts) == 4 and l2_parts[0] == "Domains"
                        and l2_parts[2] == "L2_Modules" and Path(l2_parts[3]).suffix.lower() == ".md"):
                    mapped.add(dep_rel)
                    add(path, {"kind": "changed_missing_dependency", "changed_file": dep_rel})
                continue
            dependents.setdefault(dep_rel, []).append(path)

    queue = deque(sorted(reasons))
    visited: set[str] = set()
    while queue:
        dependency = queue.popleft()
        if dependency in visited:
            continue
        visited.add(dependency)
        for dependent in sorted(set(dependents.get(dependency, []))):
            add(dependent, {"kind": "depends_on", "dependency": dependency})
            if dependent not in visited:
                queue.append(dependent)
    if not modules:
        warnings.append("No L2 documents discovered; an empty candidate list is not proof of no impact")
    return {
        "advisory": True,
        "does_not_change_acceptance": True,
        "repo_root": str(root),
        "doc_llm_root": doc_rel,
        "changed_files": changed_files,
        "candidates": [{"path": path, "reasons": reasons[path]} for path in sorted(reasons)],
        "unmapped": sorted(set(changed_files) - mapped),
        "warnings": warnings,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--doc-llm-root", help="Repository-relative root; default doc_llm, honoring its dlm.json doc_llm_root")
    parser.add_argument("--changed-file", action="append", default=[], help="Explicit repository-relative path; deleted files are supported")
    parser.add_argument("--changed-files-json", help="Explicit repository-relative UTF-8 JSON file containing an array of changed path strings")
    parser.add_argument("--json", action="store_true", dest="json_output")
    args = parser.parse_args()
    try:
        root = Path(args.repo_root).resolve()
        changed = list(args.changed_file)
        if args.changed_files_json:
            _, input_path = safe_path(root, args.changed_files_json)
            values = json.loads(input_path.read_text(encoding="utf-8-sig"))
            if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
                raise ValueError("--changed-files-json must contain a JSON array of strings")
            changed.extend(values)
        if not changed:
            raise ValueError("Provide at least one --changed-file or a nonempty --changed-files-json array")
        report = analyze(root, changed, args.doc_llm_root)
    except (OSError, ValueError, RuntimeError) as exc:
        if args.json_output:
            print(json.dumps({"advisory": True, "does_not_change_acceptance": True, "error": str(exc)}, ensure_ascii=False))
        else:
            print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    if args.json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("Advisory L2 review candidates only; does not change knowledge status or acceptance.")
        print(f"DLM root: {report['doc_llm_root']}")
        for candidate in report["candidates"]:
            print(f"[CANDIDATE] {candidate['path']}")
            for reason in candidate["reasons"]:
                print("  " + json.dumps(reason, ensure_ascii=False))
        if not report["candidates"]:
            print("No candidates found; this is not proof of no impact.")
        for path in report["unmapped"]:
            print(f"[UNMAPPED] {path}")
        for warning in report["warnings"]:
            print(f"[WARN] {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
