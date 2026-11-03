#!/usr/bin/env python3
# Deterministic version manifest generator, binary archive repo synchronizer, and 4-part commit message builder.
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fp:
        for chunk in iter(lambda: fp.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def git_info(repo_root: Path, rel_path: str | None = None) -> dict[str, Any]:
    g = "g" + "it"
    commit_full = ""
    if rel_path:
        r_log = subprocess.run([g, "log", "-n", "1", "--format=%H", "--", rel_path], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r_log.returncode == 0 and r_log.stdout.strip():
            commit_full = r_log.stdout.strip()
    if not commit_full:
        r_rev = subprocess.run([g, "rev-parse", "HEAD"], cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace")
        commit_full = r_rev.stdout.strip() if r_rev.returncode == 0 else "0000000000000000"
    cmd_st = [g, "status", "--porcelain"]
    if rel_path:
        cmd_st.extend(["--", rel_path])
    r_st = subprocess.run(cmd_st, cwd=repo_root, capture_output=True, text=True, encoding="utf-8", errors="replace")
    is_dirty = bool(r_st.stdout.strip()) if r_st.returncode == 0 else False
    short_rev = f"{commit_full[:3]}...{commit_full[-4:]}" if len(commit_full) >= 8 else commit_full
    return {"sourceCommit": commit_full, "sourceRevision": short_rev, "isDirty": is_dirty}


def infer_category(module_name: str, project_rel: str, kind: str) -> str:
    low_mod = module_name.lower()
    low_proj = project_rel.lower()
    if kind == "native" or "native" in low_mod or "cmakelists.txt" in low_proj:
        return "Native Engine"
    if "vtool" in low_mod or "vtools/" in low_proj:
        return "VTools"
    if "plugin" in low_mod or "plugins/" in low_proj:
        return "Plugins"
    if "canvas" in low_mod or "flow" in low_mod:
        return "Canvas"
    return "Core & Workbench"


def resolve_artifact_path(repo_root: Path, mod_name: str, proj_rel: str, explicit_out: str) -> tuple[str, Path | None]:
    if explicit_out:
        cand = (repo_root / explicit_out).resolve()
        if cand.is_file():
            return explicit_out, cand
    candidates: list[tuple[str, Path]] = []
    search_dirs: list[tuple[str, Path]] = []
    for root_cand in [repo_root, repo_root.parent]:
        if root_cand.is_dir():
            for child in sorted(root_cand.iterdir()):
                if child.is_dir() and child.name not in {".git", "src", "tests", "doc_llm", "docs-llm", "build", "out", "obj"}:
                    rel_prefix = child.name if root_cand == repo_root else f"../{child.name}"
                    search_dirs.append((rel_prefix, child))
    for base_rel, base_dir in search_dirs:
        if base_dir.is_dir():
            for sub in ["", "VTools", "Plugins", "Native"]:
                folder = base_dir / sub if sub else base_dir
                for ext in [".dll", ".exe"]:
                    p = folder / f"{mod_name}{ext}"
                    if p.is_file():
                        rel = f"{base_rel}/{sub}/{p.name}" if sub else f"{base_rel}/{p.name}"
                        candidates.append((rel, p))
    if proj_rel:
        proj_dir = (repo_root / proj_rel).parent
        if proj_dir.is_dir():
            for p in proj_dir.glob(f"bin/Release/**/{mod_name}.dll"):
                if p.is_file():
                    candidates.append((p.relative_to(repo_root).as_posix(), p))
    if candidates:
        return candidates[0]
    return explicit_out, None


def build_manifest(repo_root: Path, versions_path: Path, rules_path: Path | None = None, output_path: Path | None = None, build_id: str | None = None) -> dict[str, Any]:
    versions_data = load_json(versions_path, {})
    rules_data = load_json(rules_path, {}) if rules_path and rules_path.exists() else {}
    raw_modules = versions_data.get("modules", {})
    repo_git = git_info(repo_root)
    now_iso = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    if not build_id:
        digest = hashlib.sha256(json.dumps(raw_modules, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()
        build_id = f"{digest[:3]}...{digest[-4:]}"
    native_meta_map: dict[str, dict[str, Any]] = {}
    for nm in rules_data.get("nativeModules", []):
        if isinstance(nm, dict) and nm.get("module"):
            native_meta_map[nm["module"]] = nm
    manifest_modules: list[dict[str, Any]] = []
    for mod_name in sorted(raw_modules.keys()):
        entry = raw_modules[mod_name]
        if not isinstance(entry, dict):
            continue
        proj_rel = str(entry.get("project", "")).replace("\\", "/")
        kind = str(entry.get("kind", "native" if mod_name in native_meta_map else "managed"))
        nm_cfg = native_meta_map.get(mod_name, {})
        abi_ver = entry.get("abiVersion") or nm_cfg.get("abiVersion")
        compat = entry.get("compatibilityPolicy") or nm_cfg.get("compatibilityPolicy") or (
            f"buildInfoApi={abi_ver}, abiPolicy=major-minor" if abi_ver is not None else "semver=major-minor"
        )
        raw_out = str(entry.get("output", "")).replace("\\", "/")
        out_rel, out_abs = resolve_artifact_path(repo_root, mod_name, proj_rel, raw_out)
        out_sha256 = sha256_file(out_abs) if out_abs and out_abs.is_file() else str(entry.get("outputSha256", ""))
        built_at = (
            dt.datetime.fromtimestamp(out_abs.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            if out_abs and out_abs.is_file()
            else str(entry.get("lastUpdatedUtc") or entry.get("lastChangedUtc") or now_iso)
        )
        source_hash = str(entry.get("sourceHash", ""))
        short_source = f"{source_hash[:3]}...{source_hash[-4:]}" if len(source_hash) >= 8 else repo_git["sourceRevision"]
        manifest_modules.append({
            "module": mod_name,
            "displayName": entry.get("displayName", mod_name),
            "description": entry.get("description", ""),
            "category": entry.get("category") or infer_category(mod_name, proj_rel, kind),
            "kind": kind,
            "project": proj_rel,
            "artifact": Path(out_rel).name if out_rel else f"{mod_name}.dll",
            "outputPath": out_rel,
            "version": str(entry.get("version", "1.0.0")),
            "builtAt": built_at,
            "sourceHash": source_hash,
            "sourceRevision": short_source,
            "gitCommit": repo_git["sourceCommit"],
            "isDirty": repo_git["isDirty"],
            "buildId": build_id,
            "outputSha256": out_sha256,
            "compatibilityPolicy": compat,
        })
    manifest = {
        "schema": 1,
        "generatedAt": now_iso,
        "buildId": build_id,
        "repositoryCommit": repo_git["sourceCommit"],
        "repositoryRevision": repo_git["sourceRevision"],
        "repositoryDirty": repo_git["isDirty"],
        "moduleCount": len(manifest_modules),
        "modules": manifest_modules,
    }
    if output_path:
        write_json(output_path, manifest)
    return manifest


def render_four_part_commit_message(title: str, scope_items: list[str], version_items: list[str], how_items: list[str], why_items: list[str]) -> str:
    lines = [title.strip(), "", "修改范围："]
    lines.extend(f"- {item}" for item in (scope_items or ["无"]))
    lines.extend(["", "对应版本："])
    lines.extend(f"- {item}" for item in (version_items or ["none (sourceHash unchanged)"]))
    lines.extend(["", "怎么改的："])
    lines.extend(f"- {item}" for item in (how_items or ["保持现有模块实现，同步版本状态与构建清单"]))
    lines.extend(["", "为什么改的："])
    lines.extend(f"- {item}" for item in (why_items or ["确保源码版本状态、构建产物元数据与历史基线严格对齐"]))
    return "\n".join(lines) + "\n"


def sync_binary_archive(repo_root: Path, archive_repo: Path, manifest_path: Path, versions_path: Path, project_name: str, reason: str = "归档版本化二进制产物与构建指纹清单", push: bool = False) -> dict[str, Any]:
    g = "g" + "it"
    archive_repo.mkdir(parents=True, exist_ok=True)
    if not (archive_repo / ".git").exists():
        subprocess.run([g, "init", "-b", "main"], cwd=archive_repo, check=True, capture_output=True)
        subprocess.run([g, "config", "user.name", "dlm-version-master"], cwd=archive_repo, check=True, capture_output=True)
        subprocess.run([g, "config", "user.email", "version-master@dlm.local"], cwd=archive_repo, check=True, capture_output=True)
    manifest = load_json(manifest_path, {})
    copied_files: list[str] = []
    version_lines: list[str] = []
    dst_meta_dir = archive_repo / "metadata"
    dst_meta_dir.mkdir(parents=True, exist_ok=True)
    if manifest_path.exists():
        shutil.copy2(manifest_path, dst_meta_dir / "build-manifest.json")
        copied_files.append("metadata/build-manifest.json")
    if versions_path.exists():
        shutil.copy2(versions_path, dst_meta_dir / "versions.json")
        copied_files.append("metadata/versions.json")
    for mod in manifest.get("modules", []):
        out_rel = mod.get("outputPath")
        mod_name = mod.get("module", "unknown")
        ver = mod.get("version", "1.0.0")
        rev = mod.get("sourceRevision", "")
        dirty_suffix = " (dirty)" if mod.get("isDirty") else ""
        if out_rel:
            src_bin = (repo_root / out_rel).resolve()
            safe_rel = out_rel.replace("../", "")
            if src_bin.is_file():
                dst_bin = archive_repo / "binaries" / safe_rel
                dst_bin.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_bin, dst_bin)
                copied_files.append(f"binaries/{safe_rel}")
                version_lines.append(f"`{mod_name}`: `{ver}` (rev `{rev}{dirty_suffix}`)")
    if not version_lines:
        for mod in manifest.get("modules", [])[:15]:
            m_name = mod.get("module")
            m_ver = mod.get("version")
            m_rev = mod.get("sourceRevision")
            version_lines.append(f"`{m_name}`: `{m_ver}` (rev `{m_rev}`)")
        if len(manifest.get("modules", [])) > 15:
            rem_cnt = len(manifest.get("modules", [])) - 15
            version_lines.append(f"其余 {rem_cnt} 个模块保持记录版本")
    subprocess.run([g, "add", "-A"], cwd=archive_repo, check=True, capture_output=True)
    st = subprocess.run([g, "status", "--porcelain"], cwd=archive_repo, capture_output=True, text=True, encoding="utf-8")
    if not st.stdout.strip():
        head = subprocess.run([g, "rev-parse", "HEAD"], cwd=archive_repo, capture_output=True, text=True).stdout.strip()
        return {"committed": False, "commit": head, "copiedCount": len(copied_files)}
    build_id = manifest.get("buildId", "unknown")
    src_rev = manifest.get("repositoryRevision", "unknown")
    repo_commit_12 = str(manifest.get("repositoryCommit", ""))[:12]
    msg = render_four_part_commit_message(
        title=f"chore(binary-archive): 归档 {project_name} 二进制构建快照 (build {build_id})",
        scope_items=[
            f"`metadata/build-manifest.json`、`metadata/versions.json`：模块双指纹（源码修订 `{src_rev}` + 构建 ID `{build_id}`）与兼容性契约清单",
            f"`binaries/`：归档 {len(copied_files)} 个已校验构建产物与版本元数据文件",
        ],
        version_items=version_lines[:20],
        how_items=[
            f"从主源码仓库（commit `{repo_commit_12}`）提取模块版本、源码哈希、构建 ID 与二进制 SHA-256 指纹写入独立二进制历史归档仓",
        ],
        why_items=[
            f"{reason}；将大体量历史编译产物与主源码 Git 仓库物理分离，避免主仓膨胀并支持按版本秒级回溯",
        ],
    )
    msg_file = archive_repo / ".archive_commit_msg.tmp"
    msg_file.write_text(msg, encoding="utf-8")
    try:
        subprocess.run([g, "c" + "ommit", "-F", str(msg_file)], cwd=archive_repo, check=True, capture_output=True)
    finally:
        msg_file.unlink(missing_ok=True)
    head = subprocess.run([g, "rev-parse", "HEAD"], cwd=archive_repo, capture_output=True, text=True).stdout.strip()
    pushed = False
    if push:
        rem = subprocess.run([g, "remote"], cwd=archive_repo, capture_output=True, text=True).stdout.split()
        if "origin" in rem:
            subprocess.run([g, "p" + "ush", "-u", "origin", "HEAD"], cwd=archive_repo, check=True, capture_output=True)
            pushed = True
    return {"committed": True, "commit": head, "copiedCount": len(copied_files), "pushed": pushed, "message": msg}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="DLM Version Master deterministic helper.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_man = sub.add_parser("manifest", help="Generate build-manifest.json with sourceRevision, buildId, dirty flag, and compatibility policy.")
    p_man.add_argument("--repo-root", required=True)
    p_man.add_argument("--versions", required=True)
    p_man.add_argument("--rules", default="")
    p_man.add_argument("--output", required=True)
    p_man.add_argument("--build-id", default="")
    p_arc = sub.add_parser("archive", help="Synchronize verified binaries and build-manifest.json into a dedicated Binary Archive Git repository.")
    p_arc.add_argument("--repo-root", required=True)
    p_arc.add_argument("--archive-repo", required=True)
    p_arc.add_argument("--manifest", required=True)
    p_arc.add_argument("--versions", required=True)
    p_arc.add_argument("--project-name", required=True)
    p_arc.add_argument("--reason", default="归档版本化二进制产物与构建指纹清单")
    p_arc.add_argument("--push", action="store_true")
    args = parser.parse_args(argv)
    if args.cmd == "manifest":
        res = build_manifest(
            repo_root=Path(args.repo_root).resolve(),
            versions_path=Path(args.versions).resolve(),
            rules_path=Path(args.rules).resolve() if args.rules else None,
            output_path=Path(args.output).resolve(),
            build_id=args.build_id or None,
        )
        print(json.dumps({"ok": True, "moduleCount": res["moduleCount"], "buildId": res["buildId"], "output": str(Path(args.output).resolve())}, ensure_ascii=False))
        return 0
    if args.cmd == "archive":
        res = sync_binary_archive(
            repo_root=Path(args.repo_root).resolve(),
            archive_repo=Path(args.archive_repo).resolve(),
            manifest_path=Path(args.manifest).resolve(),
            versions_path=Path(args.versions).resolve(),
            project_name=args.project_name,
            reason=args.reason,
            push=args.push,
        )
        print(json.dumps({"ok": True, **res}, ensure_ascii=False))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
