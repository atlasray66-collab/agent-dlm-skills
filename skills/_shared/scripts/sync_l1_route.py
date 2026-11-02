#!/usr/bin/env python3
"""Rebuild Domain L1 route tables from L2 front matter and Reference topics."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from dlm_common import (
    PreparedWrite,
    ReadSnapshot,
    apply_prepared,
    atomic_write,
    encode_text,
    read_text,
)
try:
    from dlm_config import KNOWN_KNOWLEDGE_DIRS, resolve_knowledge_dir_name
except Exception:
    KNOWN_KNOWLEDGE_DIRS = ("docs-llm", "doc_llm", "docs_llm")
    def resolve_knowledge_dir_name(root: Path | None = None) -> str:
        return "doc_llm"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ACTIVE_DOC_LLM_DIR = os.environ.get("DLM_DOC_LLM_DIR") or resolve_knowledge_dir_name(Path.cwd())
L2_HEADING_PATTERN = r"(?:[一二三四五六七八九十]+、)?(?:L2[ 	]+)?路由表"
REFERENCE_HEADING_PATTERN = r"(?:[一二三四五六七八九十]+、)?参考资料路由"
L2_SECTION_PATTERN = rf"(##[ \t]+{L2_HEADING_PATTERN}[ \t]*\r?\n)(.*?)(?=\r?\n##[ \t]|\r?\n---[ \t]*\r?\n|\Z)"
REFERENCE_SECTION_PATTERN = rf"(##[ \t]+{REFERENCE_HEADING_PATTERN}[ \t]*\r?\n)(.*?)(?=\r?\n##[ \t]|\r?\n---[ \t]*\r?\n|\Z)"
NUMBERED_SECTION_HEADING_RE = re.compile(r"^(##[ \t]+)([一二三四五六七八九十]+)、(.+)$", re.MULTILINE)
ALLOWED_REFERENCE_STATUS = ("已归档", "部分归档", "待补充", "已废弃")
CHINESE_DIGITS = ("零", "一", "二", "三", "四", "五", "六", "七", "八", "九")
CHINESE_SECTION_NUMBERS = ("一", "二", "三", "四", "五", "六", "七", "八", "九", "十")


def write_text(path: Path, text: str, has_bom: bool, newline: str) -> None:
    atomic_write(path, encode_text(text, has_bom, newline))


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("domain_dir", nargs="?", help="Domain directory, repository-relative or absolute")
    target.add_argument("--all", action="store_true", help="Process all Domains")
    parser.add_argument("--repo-root", default=None, help="Repository root; defaults to cwd or discovered root")
    parser.add_argument("--doc-llm-root", default=None, help="Repository-relative doc_llm root")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--check", action="store_true", help="Check freshness without writing")
    return parser.parse_args(argv)


def parse_frontmatter(path: Path, snapshot: ReadSnapshot | None = None) -> dict[str, object] | None:
    content, _, _ = read_text(path, snapshot)
    match = re.match(r"^---\s*\n(.*?)\n---\s*(?:\n|\Z)", content, re.DOTALL)
    if not match:
        return None
    result: dict[str, object] = {}
    current_list: str | None = None
    for raw_line in match.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("- ") and current_list:
            cast = result.setdefault(current_list, [])
            assert isinstance(cast, list)
            cast.append(line[2:].strip().strip("\"'"))
            continue
        current_list = None
        if ":" not in line:
            continue
        key, value = (part.strip() for part in line.split(":", 1))
        value = value.split(" #", 1)[0].strip()
        if key in {"match_globs", "depends_on"}:
            if value.startswith("[") and value.endswith("]"):
                result[key] = [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
            elif not value:
                result[key] = []
                current_list = key
            else:
                result[key] = value.strip("\"'")
        else:
            result[key] = value.strip("\"'")
    return result


def first_heading(path: Path, snapshot: ReadSnapshot | None = None) -> str:
    content, _, _ = read_text(path, snapshot)
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not stripped.startswith("# {"):
            return stripped[2:].strip()
    match = re.search(r"(?m)^#\s+(.+)$", content)
    return match.group(1).strip() if match else path.stem


def generate_table(domain: Path, snapshot: ReadSnapshot | None = None) -> tuple[str, list[str]]:
    files = sorted(snapshot.members(domain / "L2_Modules", "*.md") if snapshot else (domain / "L2_Modules").glob("*.md"))
    if not files:
        return "> [WARN] No L2 files found\n", ["No L2 files found"]
    rows: list[str] = []
    errors: list[str] = []
    for file in files:
        meta = parse_frontmatter(file, snapshot)
        if meta is None:
            errors.append(f"{file.name}: missing YAML front matter")
            globs: list[str] = []
            status = "未标注"
        else:
            raw_globs = meta.get("match_globs", [])
            if not isinstance(raw_globs, list) or not all(isinstance(item, str) and item.strip() for item in raw_globs):
                errors.append(f"{file.name}: match_globs must be a string list")
                globs = []
            else:
                globs = raw_globs
            status = str(meta.get("status", "未标注"))
            if not globs:
                errors.append(f"{file.name}: match_globs is empty")
        glob_text = ", ".join(f"`{item}`" for item in globs) if globs else "—"
        rows.append(f"| {first_heading(file, snapshot)} | `L2_Modules/{file.name}` | {glob_text} | {status} |")
    header = (
        "> 本表由 `sync_l1_route.py` 从 L2 front matter 自动生成。\n"
        "> 手工修改会在下次同步时被覆盖。\n\n"
        "| 当你需要了解... | 去读 | match_globs | 状态 |\n"
        "|---|---|---|:---:|\n"
    )
    return header + "\n".join(rows) + "\n", errors


def prepare_l1(domain: Path, table: str, snapshot: ReadSnapshot) -> PreparedWrite | None:
    candidates = snapshot.members(domain, "L1_*_router.md")
    if len(candidates) != 1:
        print(f"[ERROR] Expected exactly one L1_*_router.md in {domain}, found {len(candidates)}")
        return None
    l1 = candidates[0]
    content, has_bom, newline = read_text(l1, snapshot)
    match = re.search(r"(##\s*(?:[一二三四五六七八九十]+、)?(?:L2 )?路由表[ \t]*\n)(.*?)(?=\n##\s|\Z)", content, re.DOTALL)
    if not match:
        print(f"[ERROR] Missing route table section: {l1}")
        return None
    replacement = match.group(1) + "\n" + table.rstrip("\r\n") + "\n"
    updated = content[: match.start()] + replacement + content[match.end() :]
    return PreparedWrite(l1, encode_text(updated, has_bom, newline), table, "route table")


def update_l1(domain: Path, table: str, preview: bool, validate_only: bool = False, check: bool = False) -> bool:
    snapshot = ReadSnapshot()
    item = prepare_l1(domain, table, snapshot)
    return bool(item) and (True if validate_only and not check else apply_prepared([item], snapshot, preview=preview, check=check))


def process(domain: Path, preview: bool, validate_only: bool = False, check: bool = False) -> bool:
    snapshot = ReadSnapshot()
    table, errors = generate_table(domain, snapshot)
    for error in errors:
        print(f"[ERROR] {error}")
    if errors:
        return False
    item = prepare_l1(domain, table, snapshot)
    return bool(item) and (True if validate_only and not check else apply_prepared([item], snapshot, preview=preview, check=check))

def resolve_path(path: Path) -> Path:
    return path.resolve(strict=False)


def is_path_within_root(path: Path, root: Path) -> bool:
    try:
        resolve_path(path).relative_to(resolve_path(root))
        return True
    except Exception:
        return False


def fail_path_validation(label: str, raw_value: str) -> "NoReturn":
    print(f"[ERROR] Invalid {label}: {raw_value}")
    sys.exit(1)


def ensure_path_within(path: Path, root: Path, label: str) -> Path:
    resolved = resolve_path(path)
    if not is_path_within_root(resolved, root):
        fail_path_validation(label, str(path))
    return resolved


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

DEFAULT_KNOWLEDGE_DIR = "docs-llm"

ACTIVE_DOC_LLM_DIR = os.environ.get("DLM_DOC_LLM_DIR", DEFAULT_KNOWLEDGE_DIR).replace("\\", "/").strip("/") or DEFAULT_KNOWLEDGE_DIR


def _kb_dir_for(project_root: Path) -> str:
    return resolve_knowledge_dir_name(project_root)


def resolve_domain_dir(project_root: Path, raw_domain: str) -> Path:
    kb_dir = _kb_dir_for(project_root)
    domains_root = project_root / kb_dir / "Domains"
    candidate = Path(raw_domain)
    if candidate.is_absolute():
        return ensure_path_within(candidate, domains_root, "domain directory")

    normalized = raw_domain.replace("\\", "/").strip()
    for prefix_dir in tuple(dict.fromkeys([kb_dir, ACTIVE_DOC_LLM_DIR, *KNOWN_KNOWLEDGE_DIRS])):
        prefix = f"{prefix_dir}/Domains/"
        if normalized.startswith(prefix):
            candidate = project_root / kb_dir / normalized[len(f"{prefix_dir}/"):]
            return ensure_path_within(candidate, domains_root, "domain directory")
    if normalized.startswith("Domains/"):
        candidate = project_root / kb_dir / normalized
    elif normalized and "/" not in normalized:
        candidate = domains_root / normalized
    else:
        candidate = project_root / normalized
    return ensure_path_within(candidate, domains_root, "domain directory")


def validate_domain_dir(domain_dir: Path) -> Path:
    project_root = find_project_root(resolve_path(domain_dir))
    return ensure_path_within(domain_dir, project_root / _kb_dir_for(project_root) / "Domains", "domain directory")


def find_project_root(start: Path) -> Path:
    """从脚本位置向上查找项目根目录 (包含配置的知识库目录或默认知识库目录)"""
    env_root = os.environ.get("DLM_PROJECT_ROOT")
    if env_root:
        return Path(env_root).resolve()
    candidates = tuple(dict.fromkeys([ACTIVE_DOC_LLM_DIR, *KNOWN_KNOWLEDGE_DIRS]))
    current = start
    for _ in range(10):  # 最多向上 10 层
        if (current / "dlm.config.json").is_file() or any((current / d).is_dir() for d in candidates):
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    # 回退: 使用 cwd
    cwd = Path.cwd()
    for current in [cwd, *cwd.parents]:
        if (current / "dlm.config.json").is_file() or any((current / d).is_dir() for d in candidates):
            return current
    print(f"[ERROR] Cannot find project root (no {'/ or '.join(candidates)}/ directory found)")
    sys.exit(1)


def parse_yaml_frontmatter(filepath: Path) -> dict | None:
    """解析 Markdown 文件的 YAML front-matter (简单解析, 不依赖 pyyaml)"""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        print(f"  [WARN] Cannot read {filepath}: {e}")
        return None

    # 匹配 --- ... ---
    match = re.match(r"^---\s*\n(.*?\n)---\s*\n", content, re.DOTALL)
    if not match:
        print(f"  [SKIP] {filepath.name}: no YAML front-matter")
        return None

    yaml_block = match.group(1)
    result = {}

    for line in yaml_block.split("\n"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 解析列表项: - "value"
        if line.startswith("- "):
            val = line[2:].strip().strip('"').strip("'")
            if "match_globs" in result and isinstance(result["match_globs"], list):
                result["match_globs"].append(val)
            continue

        # 解析键值对: key: value 或 key: "value"
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")

            # 去除行尾注释
            if "#" in val:
                val = val[:val.index("#")].strip().strip('"').strip("'")

            if key == "match_globs":
                result[key] = []  # 下面的 - 项会追加
                if val:  # 单行格式: match_globs: ["a", "b"]
                    if val.startswith("["):
                        items = val.strip("[]").split(",")
                        result[key] = [i.strip().strip('"').strip("'") for i in items if i.strip()]
            else:
                result[key] = val

    return result


def extract_first_heading(filepath: Path) -> str:
    """提取 Markdown 文件的第一个 # 标题作为模块描述"""
    try:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# ") and not line.startswith("# {"):
                    return line[2:].strip()
    except Exception:
        pass
    return filepath.stem


def generate_l2_route_table(domain_dir: Path) -> str:
    """为指定 Domain 生成 L2 路由表 Markdown"""
    domain_dir = validate_domain_dir(domain_dir)
    l2_dir = domain_dir / "L2_Modules"
    if not l2_dir.exists():
        return f"> [WARN] `{l2_dir}` directory not found\n"

    l2_files = sorted(l2_dir.glob("*.md"))
    if not l2_files:
        return "> [WARN] No L2 files found\n"

    rows = []
    for f in l2_files:
        meta = parse_yaml_frontmatter(f)
        heading = extract_first_heading(f)

        if meta:
            globs = meta.get("match_globs", [])
            status = meta.get("status", "未标注")
            globs_str = ", ".join(f"`{g}`" for g in globs) if globs else "—"
        else:
            globs_str = "—"
            status = "未标注"

        rows.append(
            f"| {heading} | `L2_Modules/{f.name}` | {globs_str} | {status} |"
        )

    header = (
        "> 本表由 `dlm kb route` 从 L2 YAML front-matter 自动生成。\n"
        "> 手动修改将在下次运行脚本时被覆盖。\n\n"
        "| 当你需要了解... | 去读 | match_globs | 状态 |\n"
        "|---|---|---|:---:|\n"
    )

    return header + "\n".join(rows) + "\n"


def generate_reference_route_table(domain_dir: Path) -> str | None:
    """为指定 Domain 生成参考资料路由 Markdown"""
    domain_dir = validate_domain_dir(domain_dir)
    ref_dir = domain_dir / "references"
    if not ref_dir.exists():
        return None

    topic_readmes = sorted(ref_dir.glob("*/README.md"))
    if not topic_readmes:
        return None

    rows = []
    for readme in topic_readmes:
        meta = parse_yaml_frontmatter(readme)
        heading = extract_first_heading(readme)
        rel_path = readme.relative_to(domain_dir).as_posix()

        if meta:
            globs = meta.get("match_globs", [])
            reference_type = meta.get("reference_type", "未标注")
            authority = meta.get("authority", "未标注")
            status = meta.get("status", "未标注")
            globs_str = ", ".join(f"`{g}`" for g in globs) if globs else "—"
        else:
            globs_str = "—"
            reference_type = "未标注"
            authority = "未标注"
            status = "未标注"

        rows.append(
            f"| {heading} | `{rel_path}` | {reference_type} | {authority} | {globs_str} | {status} |"
        )

    header = (
        "> 本表由 `dlm kb route` 从 `references/*/README.md` 的 YAML front-matter 自动生成。\n"
        "> 只把 topic README 作为入口; topic 内原文在执行阶段按目录卡继续下钻。\n\n"
        "| 当你需要查阅... | 去读 | 类型 | 权威性 | match_globs | 状态 |\n"
        "|---|---|---|---|---|:---:|\n"
    )

    return header + "\n".join(rows) + "\n"


def replace_section(content: str, pattern: str, section_body: str) -> tuple[str, bool]:
    """替换 Markdown 二级标题段落内容"""
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content, False

    normalized = section_body.rstrip("\r\n")
    next_section = content[match.end(0):].lstrip("\r\n")
    new_content = (
        content[:match.end(1)]
        + "\n"
        + normalized
        + "\n\n"
        + next_section
    )
    return new_content, True


def remove_section(content: str, pattern: str) -> tuple[str, bool]:
    """删除 Markdown 二级标题段落内容"""
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return content, False

    before = content[:match.start(0)].rstrip("\r\n")
    after = content[match.end(0):].lstrip("\r\n")
    if before and after:
        return before + "\n\n" + after, True
    return before + after, True


def format_chinese_section_number(number: int) -> str:
    """将 1-based 编号格式化为中文章节序号"""
    if 1 <= number <= len(CHINESE_SECTION_NUMBERS):
        return CHINESE_SECTION_NUMBERS[number - 1]
    raise ValueError(f"Unsupported section number: {number}")


def normalize_l1_numbering(content: str) -> str:
    """按实际保留的章节重排已有编号，不给无编号的标题添加编号。"""
    number = 0

    def renumber(match: re.Match) -> str:
        nonlocal number
        number += 1
        return f"## {format_chinese_section_number(number)}、{match.group(1)}"

    return re.sub(r"^##[ \t]+[一二三四五六七八九十]+、(.*)$", renumber, content, flags=re.MULTILINE)


def update_l1_file(domain_dir: Path, l2_table: str, reference_table: str | None) -> bool:
    """在 L1 路由文件中替换 L2 / 参考资料路由段落"""
    domain_dir = validate_domain_dir(domain_dir)
    # 查找 L1 文件
    l1_candidates = list(domain_dir.glob("L1_*_router.md"))
    if not l1_candidates:
        print(f"  [ERROR] No L1_*_router.md found in {domain_dir}")
        return False

    l1_path = l1_candidates[0]
    print(f"  L1: {l1_path.name}")

    try:
        with open(l1_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
    except Exception as e:
        print(f"  [ERROR] Cannot read {l1_path}: {e}")
        return False

    new_content, replaced_l2 = replace_section(content, L2_SECTION_PATTERN, l2_table)
    if not replaced_l2:
        print(f"  [WARN] No '## L2 路由表' section found, skipping")
        return False

    if reference_table:
        updated_content, replaced_ref = replace_section(
            new_content,
            REFERENCE_SECTION_PATTERN,
            reference_table,
        )
        if replaced_ref:
            new_content = updated_content
        else:
            l2_match = re.search(L2_SECTION_PATTERN, new_content, re.DOTALL)
            if not l2_match:
                print("  [WARN] L2 route section disappeared during update, skipping reference insertion")
                return False
            numbered = re.match(r"##[ \t]+[一二三四五六七八九十]+、", l2_match.group(1))
            ref_heading = "## 一、参考资料路由" if numbered else "## 参考资料路由"
            before = new_content[:l2_match.end(0)].rstrip("\r\n")
            after = new_content[l2_match.end(0):].lstrip("\r\n")
            insertion = ref_heading + "\n\n" + reference_table.rstrip("\r\n")
            new_content = before + "\n\n" + insertion + "\n\n" + after
    else:
        new_content, _ = remove_section(new_content, REFERENCE_SECTION_PATTERN)

    new_content = normalize_l1_numbering(new_content)

    try:
        # Preserve the file's existing BOM and newline representation.
        raw = l1_path.read_bytes()
        encoding = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
        newline = "\r\n" if b"\r\n" in raw else "\n"
        with open(l1_path, "w", encoding=encoding, newline=newline) as f:
            f.write(new_content)
        print(f"  [OK] Route tables updated")
        return True
    except Exception as e:
        print(f"  [ERROR] Write failed: {e}")
        return False


def process_domain(domain_dir: Path, preview: bool = False) -> bool:
    """处理单个 Domain"""
    domain_dir = validate_domain_dir(domain_dir)
    print(f"\n{'='*60}")
    print(f"Domain: {domain_dir.name}")
    print(f"{'='*60}")

    l2_table = generate_l2_route_table(domain_dir)
    ref_table = generate_reference_route_table(domain_dir)

    print(f"\n[L2 路由表]\n{l2_table}")
    if ref_table:
        print(f"\n[参考资料路由]\n{ref_table}")
    else:
        print("\n[参考资料路由]\n> [INFO] No reference topics found\n")

    if preview:
        print("  [PREVIEW] Preview mode, no files written")
        return True

    return update_l1_file(domain_dir, l2_table, ref_table)


def print_usage() -> None:
    """Print usage with the actual invoked entrypoint path."""
    entry = os.environ.get("DLM_SKILL_ENTRYPOINT") or Path(sys.argv[0]).as_posix()
    print("Usage:")
    print(f"  python {entry} <domain_dir> [--preview]")
    print(f"  python {entry} --all [--preview]")
    print(f"  python {entry} --help")
    print("")
    print("Examples:")
    print(f"  python {entry} {_kb_dir_for(find_project_root())}/Domains/1_core_runtime")
    print(f"  python {entry} --all --preview")




def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.repo_root is not None or args.check or args.doc_llm_root is not None:
        repo_root = Path(args.repo_root or ".").resolve()
        doc_rel = args.doc_llm_root or "doc_llm"
        doc_root = (repo_root / doc_rel).resolve()
        domains_root = doc_root / "Domains"
        if not is_within(doc_root, repo_root) or not domains_root.is_dir():
            print(f"[ERROR] Invalid Domains root: {domains_root}")
            return 1
        snapshot = ReadSnapshot(allowed_root=doc_root)
        if args.all:
            domains = list(snapshot.members(domains_root, "*", "dir"))
        else:
            target = Path(args.domain_dir)
            domains = [(target if target.is_absolute() else repo_root / target).resolve()]
        if not domains:
            print("[ERROR] No Domain directories found")
            return 1
        ok = True
        prepared = []
        for domain in domains:
            if not is_within(domain, domains_root) or not domain.is_dir():
                print(f"[ERROR] Domain must be inside doc_llm/Domains: {domain}")
                ok = False
                continue
            table, errors = generate_table(domain, snapshot)
            for error in errors:
                print(f"[ERROR] {error}")
            if errors:
                ok = False
                continue
            item = prepare_l1(domain, table, snapshot)
            if item:
                prepared.append(item)
            else:
                ok = False
        if not ok:
            return 1
        return 0 if apply_prepared(prepared, snapshot, preview=args.preview, check=args.check) else 1

    # Remote CLI mode (when invoked without --repo-root / --check, e.g. via dlm kb route)
    project_root = find_project_root(Path(__file__).resolve().parent)
    doc_llm_dir = project_root / _kb_dir_for(project_root)
    if args.all:
        domains_dir = doc_llm_dir / "Domains"
        if not domains_dir.exists():
            print(f"[ERROR] {domains_dir} not found")
            return 1
        domain_dirs = sorted([d for d in domains_dir.iterdir() if d.is_dir()])
        if not domain_dirs:
            print("[ERROR] No domain directories found")
            return 1
        results = {d.name: process_domain(d, args.preview) for d in domain_dirs}
        return 0 if all(results.values()) else 1
    else:
        domain_path = resolve_domain_dir(project_root, args.domain_dir)
        if not domain_path.exists():
            print(f"[ERROR] {domain_path} not found")
            return 1
        return 0 if process_domain(domain_path, args.preview) else 1


def main() -> int:
    try:
        return run()
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
