#!/usr/bin/env python3
"""Create a portable practice bundle from one course directory.

The bundle is deliberately source-oriented: it contains the practice brief,
answers, integration contract, and explicitly listed starter/reference files.
Generated builds, caches, personal practice state, and private paths are never
copied. ZIP timestamps are fixed so the same source tree produces comparable
archives.
"""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
COURSES = ROOT / "knowledge-sets"
DEFAULT_EXCLUDES = {
    ".git", ".practice", "__pycache__", "dist", "Build", "Builds", "Library",
    "Temp", "Logs", "Obj", "Binaries", "DerivedDataCache", "Intermediate", "Saved",
}
PUBLIC_SUFFIXES = {
    ".md", ".txt", ".json", ".csv", ".tsv", ".xml", ".yaml", ".yml", ".toml",
    ".py", ".c", ".h", ".cpp", ".hpp", ".cs", ".java", ".js", ".ts", ".lua", ".sql",
    ".shader", ".hlsl", ".glsl", ".compute", ".sh", ".ps1", ".cmake", ".unity",
    ".prefab", ".asset", ".meta", ".uproject", ".uplugin", ".png", ".jpg", ".jpeg",
    ".webp", ".svg", "",
}


def safe_relative(value: str) -> Path:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"bundle path must stay inside the course: {value!r}")
    return path


def load_manifest(course: str) -> tuple[Path, dict]:
    base = COURSES / course
    manifest_path = base / "practice-bundle.json"
    if not base.is_dir():
        raise FileNotFoundError(f"course directory not found: {base}")
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"{course} has no practice-bundle.json; add an explicit bundle manifest first"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 1:
        raise ValueError(f"{manifest_path}: unsupported schema {manifest.get('schema')!r}")
    if manifest.get("slug") != course:
        raise ValueError(f"{manifest_path}: slug must be {course!r}")
    if not manifest.get("include"):
        raise ValueError(f"{manifest_path}: include must not be empty")
    return base, manifest


def iter_files(base: Path, relative: Path, excludes: set[str]) -> list[tuple[Path, str]]:
    source = (base / relative).resolve()
    if not source.is_relative_to(base.resolve()):
        raise ValueError(f"path escapes course directory: {relative}")
    if not source.exists():
        raise FileNotFoundError(f"bundle input does not exist: {relative}")
    if source.is_file():
        return [(source, relative.as_posix())]

    files: list[tuple[Path, str]] = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(base)
        if any(part in excludes or part.startswith(".") for part in rel.parts):
            continue
        if path.suffix.lower() not in PUBLIC_SUFFIXES:
            continue
        files.append((path, rel.as_posix()))
    return files


def generated_readme(course: str, manifest: dict, entries: list[tuple[str, str, str]]) -> str:
    lines = [
        f"# {manifest.get('title', course)}实践包",
        "",
        "这是由 `scripts/package_practice.py` 生成的可迁移实践包。默认同时包含题面、折叠答案、集成契约和课程明确列出的起始/参考文件。",
        "",
        "## 使用顺序",
        "",
        "1. 先阅读 `brief/` 与 `course/README.md`，确认课程前置和最小版本；",
        "2. 按 `integration-contract/` 的接缝说明复制或导入文件，不要把所有代码直接丢进 Unity `Assets/`；",
        "3. 先使用 `starter/` 完成实践，再按需要查看 `answers/` 和 `reference/`；",
        "4. 运行包内命令并保存测试、日志、截图或性能数据作为验收证据。",
        "",
        "> 参考实现用于自学后的对照，不代表唯一答案。若课程标记为 `starter-and-reference`，表示当前课程代码尚未拆分起始骨架与完整解法。",
        "",
        "## 内容",
        "",
        "| 路径 | 角色 | 来源 |",
        "|---|---|---|",
    ]
    for destination, role, source in entries:
        lines.append(f"| `{destination}` | {role} | `{source}` |")
    lines.extend(["", "## 安全边界", "", "包内不应包含构建缓存、个人状态、密钥、用户绝对路径或平台专属发布产物。"])
    return "\n".join(lines) + "\n"


def build_bundle(course: str, output: Path) -> Path:
    base, manifest = load_manifest(course)
    excludes = DEFAULT_EXCLUDES | set(manifest.get("exclude", []))
    root_name = manifest.get("bundleName", f"{course}-practice")
    entries: list[tuple[str, str, str]] = []
    files_to_write: list[tuple[Path, str]] = []
    seen: set[str] = set()

    for item in manifest["include"]:
        if not isinstance(item, dict) or "path" not in item or "role" not in item:
            raise ValueError("each include item needs path and role")
        relative = safe_relative(item["path"])
        role = str(item["role"])
        for source, source_rel in iter_files(base, relative, excludes):
            if source_rel in seen:
                continue
            seen.add(source_rel)
            if source.suffix.lower() not in PUBLIC_SUFFIXES:
                raise ValueError(f"unsupported public file type in bundle: {source_rel}")
            if role == "answers":
                destination = f"answers/{source_rel}"
            elif role == "starter":
                destination = f"starter/{source_rel}"
            elif role == "reference":
                destination = f"reference/{source_rel}"
            elif role == "starter-and-reference":
                destination = f"starter-reference/{source_rel}"
            elif role == "integration-contract":
                destination = f"integration-contract/{source_rel}"
            elif role == "brief":
                destination = f"brief/{source_rel}"
            else:
                destination = f"course/{source_rel}"
            files_to_write.append((source, destination))
            entries.append((destination, role, source_rel))

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(
            zipfile.ZipInfo(f"{root_name}/README.md", date_time=(1980, 1, 1, 0, 0, 0)),
            generated_readme(course, manifest, entries),
        )
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        archive.writestr(
            zipfile.ZipInfo(f"{root_name}/manifest.json", date_time=(1980, 1, 1, 0, 0, 0)),
            manifest_bytes,
        )
        for source, destination in sorted(files_to_write, key=lambda pair: pair[1]):
            info = zipfile.ZipInfo(f"{root_name}/{destination}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | (source.stat().st_mode & 0o755)) << 16
            archive.writestr(info, source.read_bytes())
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", required=True, help="course slug from roadmap/course-index.json")
    parser.add_argument("--output", type=Path, required=True, help="output .zip path")
    args = parser.parse_args()
    try:
        output = build_bundle(args.course, args.output)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"PACKAGE FAILED: {exc}", file=sys.stderr)
        return 1
    print(f"PACKAGE OK: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
