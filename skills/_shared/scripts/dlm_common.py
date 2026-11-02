"""Small shared DLM parsing and guarded derived-file writes.

Snapshot comparisons are not compare-and-swap. Callers still need one writer;
atomic replacement protects one file, not a transaction across several files.
"""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


def current_meta(content: str) -> str:
    content = content.replace("\r\n", "\n").replace("\r", "\n")
    explicit = re.search(r"(?mi)^##[ \t]+Meta[ \t]*(?:\n|\Z)([\s\S]*?)(?=^##\s|\Z)", content)
    if explicit:
        return explicit[1]
    return re.split(r"(?m)^##\s", content, maxsplit=1)[0]


def parse_task_meta(content: str, fallback_title: str = "") -> dict[str, str]:
    """Explicit Meta is authoritative, including when a field is absent."""
    scope = current_meta(content)
    result = {"title": fallback_title, "status": "", "priority": "", "depends": ""}
    heading = re.search(r"(?m)^#\s+(.+)$", content)
    if heading:
        result["title"] = re.sub(r"^S\d+[a-z]?:\s*", "", heading[1].strip())
    for key, dest in (("状态", "status"), ("优先级", "priority"), ("依赖|前置依赖", "depends")):
        match = re.search(rf"(?m)^\|\s*(?:{key})\s*\|\s*([^|]+)\|", scope)
        if match:
            result[dest] = match[1].strip()
    if not result["status"]:
        legacy = re.search(r"(?m)^>\s*\*\*状态\*\*:\s*([^\r\n]+)", scope)
        if legacy:
            result["status"] = legacy[1].strip()
    return result


def decode_text(raw: bytes) -> tuple[str, bool, str]:
    text = raw.decode("utf-8-sig")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n").replace("\r", "\n"), raw.startswith(b"\xef\xbb\xbf"), newline


def encode_text(text: str, has_bom: bool, newline: str) -> bytes:
    payload = text.replace("\r\n", "\n").replace("\r", "\n").replace("\n", newline).encode("utf-8")
    return (b"\xef\xbb\xbf" if has_bom else b"") + payload


@dataclass
class ReadSnapshot:
    files: dict[Path, bytes | None] = field(default_factory=dict)
    directories: dict[tuple[Path, str, str], tuple[Path, ...]] = field(default_factory=dict)
    allowed_root: Path | None = None

    def __post_init__(self) -> None:
        if self.allowed_root is not None:
            self.allowed_root = self.allowed_root.resolve()

    def _check_path(self, path: Path) -> Path:
        path = path.absolute()
        if self.allowed_root is not None:
            try:
                path.resolve().relative_to(self.allowed_root)
            except ValueError:
                raise ValueError(f"Path resolves outside allowed DLM root: {path}") from None
        return path

    def read(self, path: Path) -> bytes:
        path = self._check_path(path)
        if path not in self.files:
            self.files[path] = path.read_bytes()
        value = self.files[path]
        if value is None:
            raise FileNotFoundError(path)
        return value

    def optional(self, path: Path) -> bytes | None:
        path = self._check_path(path)
        if path not in self.files:
            self.files[path] = path.read_bytes() if path.is_file() else None
        return self.files[path]

    def _members(self, directory: Path, pattern: str, kind: str) -> tuple[Path, ...]:
        directory = self._check_path(directory)
        members = []
        for path in directory.glob(pattern):
            path = self._check_path(path)
            if kind == "all" or (path.is_dir() if kind == "dir" else path.is_file()):
                members.append(path)
        return tuple(sorted(members))

    def members(self, directory: Path, pattern: str, kind: str = "all") -> tuple[Path, ...]:
        key = (self._check_path(directory), pattern, kind)
        if key not in self.directories:
            self.directories[key] = self._members(*key)
        return self.directories[key]

    def validate(self) -> None:
        for path, before in self.files.items():
            self._check_path(path)
            now = path.read_bytes() if path.is_file() else None
            if now != before:
                raise ValueError(f"Input changed during preparation; rerun: {path}")
        for key, before in self.directories.items():
            if self._members(*key) != before:
                raise ValueError(f"Directory members changed during preparation; rerun: {key[0]} ({key[1]})")


def read_text(path: Path, snapshot: ReadSnapshot | None = None) -> tuple[str, bool, str]:
    return decode_text(snapshot.read(path) if snapshot else path.read_bytes())


def atomic_write(path: Path, payload: bytes) -> None:
    """Replace one file only after its same-directory temporary is complete."""
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".dlm-", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@dataclass
class PreparedWrite:
    path: Path
    payload: bytes
    preview: str
    label: str


def apply_prepared(prepared: list[PreparedWrite], snapshot: ReadSnapshot, *, preview: bool = False, check: bool = False) -> bool:
    """Validate all inputs, then replace individually under the outer single-writer rule."""
    try:
        snapshot.validate()
        if check:
            stale = [item for item in prepared if snapshot.files[item.path.absolute()] != item.payload]
            for item in stale:
                print(f"[ERROR] Stale {item.label}: {item.path}")
            return not stale
        if preview:
            for item in prepared:
                print(item.preview)
            return True
        for item in prepared:
            # Recheck between files; prior successful derived writes are expected.
            snapshot.validate()
            if snapshot.files[item.path.absolute()] == item.payload:
                print(f"[OK] Unchanged {item.path}")
                continue
            atomic_write(item.path, item.payload)
            snapshot.files[item.path.absolute()] = item.payload
            print(f"[OK] Updated {item.path}")
        return True
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"[ERROR] {exc}")
        return False
