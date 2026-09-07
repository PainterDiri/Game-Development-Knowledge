#!/usr/bin/env python3
"""Create a portable, code-first practice download from one course directory.

The website remains the source of truth for lessons, practice instructions,
questions, answers, and explanations. The ZIP contains only explicitly
whitelisted code, tests, fixtures, configuration, and supporting materials.
Generated builds, caches, personal state, private paths, and secrets are never
copied. ZIP timestamps are fixed for reproducible packaging.
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
    "editable-baseline": "workspace",
    "reference-code": "reference",
    "test-fixture": "fixtures",
    "supporting-material": "materials",
    "license": "licenses",
}


def safe_relative(value: str) -> Path:
    if not isinstance(value, str) or not value:
        raise ValueError(f"bundle path must be a non-empty string: {value!r}")
    if value != value.strip() or "\\" in value or "\0" in value:
        raise ValueError(f"bundle path must use a portable relative form: {value!r}")
    parts = value.split("/")
    windows_forbidden = set('<>:"|?*')
    if (
        any(part in {"", ".", ".."} for part in parts)
        or any(part.endswith((" ", ".")) for part in parts)
        or any(any(ord(char) < 32 or char in windows_forbidden for char in part) for part in parts)
    ):
        raise ValueError(f"bundle path must stay inside the course and be portable: {value!r}")
    return Path(*parts)


def load_manifest(course: str) -> tuple[Path, dict]:
    course_path = safe_relative(course)
    if len(course_path.parts) != 1:
        raise ValueError(f"course slug must be one portable directory name: {course!r}")
    base = COURSES / course_path
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
    quick_start = manifest.get("quickStart", [])
    if not isinstance(quick_start, list) or not quick_start or not all(isinstance(x, str) and x for x in quick_start):
        raise ValueError(f"{manifest_path}: quickStart must be a non-empty string list")
    return base, manifest


def iter_files(base: Path, relative: Path, excludes: set[str]) -> list[tuple[Path, str]]:
    source = (base / relative).resolve()
    base_resolved = base.resolve()
    if not source.is_relative_to(base_resolved):
        raise ValueError(f"path escapes course directory: {relative}")
    if not source.exists():
        raise FileNotFoundError(f"bundle input does not exist: {relative}")
    if source.is_symlink():
        raise ValueError(f"bundle input must not be a symlink: {relative}")
    if source.is_file():
        return [(source, relative.as_posix())]

    files: list[tuple[Path, str]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"bundle input tree must not contain symlinks: {path.relative_to(base_resolved)}")
        if not path.is_file():
            continue
        rel = path.relative_to(base_resolved)
        if any(part in excludes or part.startswith(".") for part in rel.parts):
            continue
        if path.suffix.lower() not in PUBLIC_SUFFIXES:
            continue
        files.append((path, rel.as_posix()))
    return files


def generated_readme(course: str, manifest: dict, entries: list[tuple[str, str, str]]) -> str:
    workspaces = sorted({"/".join(destination.split("/")[:2])
                         for destination, role, _ in entries
                         if role in {"editable-baseline", "starter-code"}})
    lines = [
        f"# {manifest.get('title', course)}：START HERE",
        "",
        "本包可直接解压到任意个人目录，不要求克隆课程仓库。课程正文、章末题、实践约束和完整解析仍以学习网站为准；本包只承载白名单中的代码、测试、fixture 与配置。",
        "",
        "## 1. 选择工作目录",
        "",
    ]
    if workspaces:
        lines.append("从下面的可编辑目录开始，不要在 `reference/` 中作答：")
        lines.append("")
        lines.extend(f"- `{path}/`" for path in workspaces)
    else:
        lines.append("本包没有预制 starter。先复制 `reference/<project>/` 到包外自己的短路径，再在副本中工作；`reference/` 只用于对照。")
    lines.extend([
        "",
        "建议路径示例：`~/game-labs/<course>/`，或 Windows 的 `C:\\game-labs\\<course>\\`。避免把个人答案写回课程仓库、云同步冲突目录或引擎缓存目录。",
        "",
        "## 2. 先跑基线",
        "",
        "在可编辑目录中执行：",
        "",
        "```text",
        *manifest["quickStart"],
        "```",
        "",
        "先确认基线现象与网站说明一致，再开始删除、补全、改写或故障注入。绿色基线不是完成实践，只证明下载和环境入口可用。",
        "",
        "## 3. 参考区与恢复",
        "",
        "- `workspace/` 或 `starter/`：可编辑工作区；",
        "- `reference/`：只读对照，不是唯一正确答案；",
        "- `fixtures/`、`materials/`：测试输入或操作材料；",
        "- 改坏后优先用版本控制或重新解压恢复，不要覆盖自己唯一的成果。",
        "",
        "如果你已经克隆课程仓库，也可以用 `scripts/init_practice.py` 复制到被忽略的 `.practice/<course>/`；这只是备选。此时必须运行 `git check-ignore` 和 `git status`，且不得使用 `git add -f`。",
        "",
        "## 包内清单",
        "",
        "| 路径 | 角色 | 课程源 |",
        "|---|---|---|",
    ])
    for destination, role, source in entries:
        lines.append(f"| `{destination}` | `{role}` | `{source}` |")
    lines.extend([
        "",
        "## 公开与安全边界",
        "",
        "- 不包含课程网页正文、折叠解析、个人进度或个人练习目录；",
        "- 不包含构建缓存、平台发布产物、日志、密钥、用户绝对路径或未审查生成文件；",
        "- ZIP 中的测试通过只证明这份基线在声明环境下可运行，不证明学习者已经掌握，也不证明所有平台都通过。",
        "",
    ])
    return "\n".join(lines)


def build_bundle(course: str, output: Path) -> Path:
    base, manifest = load_manifest(course)
    excludes = DEFAULT_EXCLUDES | set(manifest.get("exclude", []))
    root_path = safe_relative(manifest.get("bundleName", f"{course}-code"))
    if len(root_path.parts) != 1:
        raise ValueError("bundleName must be one portable directory name")
    root_name = root_path.as_posix()
    entries: list[tuple[str, str, str]] = []
    files_to_write: list[tuple[Path, str]] = []
    seen_destinations: set[str] = set()

    for item in manifest["include"]:
        if not isinstance(item, dict) or "path" not in item or "role" not in item:
            raise ValueError("each include item needs path and role")
        relative = safe_relative(item["path"])
        role = str(item["role"])
        if role not in ROLE_DESTINATIONS:
            raise ValueError(f"unsupported bundle role {role!r}; use one of {sorted(ROLE_DESTINATIONS)}")
        destination_root = ROLE_DESTINATIONS[role]
        target = safe_relative(item.get("target", relative.name))
        item_source = base / relative
        for source, source_rel in iter_files(base, relative, excludes):
            inside = Path(source_rel).relative_to(relative) if item_source.is_dir() else Path(source.name)
            destination = (Path(destination_root) / target / inside).as_posix()
            if destination in seen_destinations:
                raise ValueError(f"duplicate bundle destination: {destination}")
            seen_destinations.add(destination)
            if source.suffix.lower() not in PUBLIC_SUFFIXES:
                raise ValueError(f"unsupported public file type in bundle: {source_rel}")
            files_to_write.append((source, destination))
            entries.append((destination, role, source_rel))

    if not files_to_write:
        raise ValueError("manifest include paths produced no public files")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        start_here = generated_readme(course, manifest, entries)
        start_info = zipfile.ZipInfo(f"{root_name}/START_HERE.md", date_time=(1980, 1, 1, 0, 0, 0))
        start_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(start_info, start_here)
        readme_info = zipfile.ZipInfo(f"{root_name}/README.md", date_time=(1980, 1, 1, 0, 0, 0))
        readme_info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(readme_info, "# Practice bundle\n\nOpen `START_HERE.md` before editing files.\n")
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
