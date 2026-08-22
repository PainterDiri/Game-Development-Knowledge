#!/usr/bin/env python3
"""Create a portable, code-first practice download from one course directory.

The website remains the source of truth for lessons, practice instructions,
questions, answers, and explanations. The ZIP generated here is intentionally
smaller: it contains only explicitly whitelisted runnable code, tests, fixtures,
configuration, and integration contracts that a learner can download and copy
into a personal project.

Generated builds, caches, personal practice state, private paths, and secrets
are never copied. ZIP timestamps are fixed so the same source tree produces
comparable archives.
"""
from __future__ import annotations

import argparse
import json
import stat
import sys
import zipfile
from pathlib import Path

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
ROLE_DESTINATIONS = {
    "code": "code",
    "starter-code": "starter",
    "reference-code": "reference",
    "test-fixture": "fixtures",
    "integration-contract": "contracts",
    "supporting-material": "materials",
    "license": "licenses",
}


def safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"bundle path must be a non-empty string: {value!r}")
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path == Path("."):
        raise ValueError(f"bundle path must stay inside the course: {value!r}")
    return path


def load_manifest(course: str) -> tuple[Path, dict]:
    base = COURSES / course
    manifest_path = base / "practice-bundle.json"
    if not base.is_dir():
        raise FileNotFoundError(f"course directory not found: {base}")
    if not manifest_path.is_file():
        raise FileNotFoundError(
            f"{course} has no practice-bundle.json; add an explicit download manifest first"
        )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != 2:
        raise ValueError(f"{manifest_path}: unsupported schema {manifest.get('schema')!r}; expected 2")
    if manifest.get("downloadType") != "practice-code":
        raise ValueError(f"{manifest_path}: downloadType must be 'practice-code'")
    if manifest.get("slug") != course:
        raise ValueError(f"{manifest_path}: slug must be {course!r}")
    if not manifest.get("include"):
        raise ValueError(f"{manifest_path}: include must not be empty")
    return base, manifest


def iter_files(base: Path, relative: Path, excludes: set[str]) -> list[tuple[Path, str]]:
    source = (base / relative).resolve()
    base_resolved = base.resolve()
    if not source.is_relative_to(base_resolved):
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
        f"# {manifest.get('title', course)}：实践代码下载包",
        "",
        "这是由 `scripts/package_practice.py` 生成的代码优先下载包。课程正文、实践题面、提示、答案和完整解释继续放在学习网站的课程页面中；本包只提供可运行代码、测试、fixture、配置和主项目接入契约。",
        "",
        "## 推荐使用顺序",
        "",
        "1. 在网站课程页阅读实践目标、约束、验收和失败诊断；",
        "2. 解压本包，在包内的 `starter/` 或 `code/` 中开始修改；若只有 `reference/`，请把它当作可运行参考基线，不要把它误认为未完成的起始骨架；",
        "3. 先按代码目录中的 README、Makefile 或命令运行测试，再逐步完成网站题面；",
        "4. 需要接入自己的 Unity `RogueSlice` 时，只按 `contracts/` 中的输入/输出、所有权、回滚和冒烟验收复制结果，不要覆盖整个项目。",
        "",
        "## 包内内容",
        "",
        "| 路径 | 角色 | 来源 |",
        "|---|---|---|",
    ]
    for destination, role, source in entries:
        lines.append(f"| `{destination}` | `{role}` | `{source}` |")
    lines.extend([
        "",
        "## 公开边界",
        "",
        "- 不包含课程网页正文、折叠答案、个人进度或个人练习目录；",
        "- 不包含构建缓存、平台发布产物、日志、密钥、用户绝对路径或未审查的生成文件；",
        "- 参考实现不是唯一正确答案，评价仍以网站中的约束、验收证据和可复现性为准；",
        "",
    ])
    return "\n".join(lines)


def build_bundle(course: str, output: Path) -> Path:
    base, manifest = load_manifest(course)
    excludes = DEFAULT_EXCLUDES | set(manifest.get("exclude", []))
    root_name = manifest.get("bundleName", f"{course}-code")
    entries: list[tuple[str, str, str]] = []
    files_to_write: list[tuple[Path, str]] = []
    seen: set[str] = set()

    for item in manifest["include"]:
        if not isinstance(item, dict) or "path" not in item or "role" not in item:
            raise ValueError("each include item needs path and role")
        relative = safe_relative(item["path"])
        role = str(item["role"])
        if role not in ROLE_DESTINATIONS:
            raise ValueError(f"unsupported bundle role {role!r}; use one of {sorted(ROLE_DESTINATIONS)}")
        destination_root = ROLE_DESTINATIONS[role]
        for source, source_rel in iter_files(base, relative, excludes):
            if source_rel in seen:
                continue
            seen.add(source_rel)
            if source.suffix.lower() not in PUBLIC_SUFFIXES:
                raise ValueError(f"unsupported public file type in bundle: {source_rel}")
            destination = f"{destination_root}/{source_rel}"
            files_to_write.append((source, destination))
            entries.append((destination, role, source_rel))

    if not files_to_write:
        raise ValueError("manifest include paths produced no public files")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        readme_info = zipfile.ZipInfo(f"{root_name}/README.md", date_time=(1980, 1, 1, 0, 0, 0))
        readme_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(readme_info, generated_readme(course, manifest, entries))
        manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
        manifest_info = zipfile.ZipInfo(f"{root_name}/manifest.json", date_time=(1980, 1, 1, 0, 0, 0))
        manifest_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(manifest_info, manifest_bytes)
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
