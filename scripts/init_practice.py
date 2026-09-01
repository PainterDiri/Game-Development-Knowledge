#!/usr/bin/env python3
"""Copy a course's public practice code into the ignored personal practice area."""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURSES = ROOT / "knowledge-sets"
PRACTICE = ROOT / ".practice"
COPY_ROLES = ("starter-code", "reference-code", "code", "test-fixture", "supporting-material")


def fail(message: str) -> int:
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


def ignored(path: Path) -> bool:
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-q", rel],
        cwd=ROOT,
        check=False,
    )
    return result.returncode == 0


def select_source(course: str, explicit: str | None) -> Path:
    base = COURSES / course
    if not base.is_dir():
        raise ValueError(f"unknown course: {course}")
    if explicit:
        relative = Path(explicit)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("--source must stay inside the course directory")
        source = base / relative
        if not source.exists():
            raise ValueError(f"source does not exist: {source.relative_to(ROOT)}")
        return source

    manifest_path = base / "practice-bundle.json"
    if not manifest_path.is_file():
        raise ValueError("course has no practice-bundle.json; pass --source explicitly")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for role in COPY_ROLES:
        for item in manifest.get("include", []):
            if item.get("role") == role:
                source = base / item["path"]
                if source.exists():
                    return source
    raise ValueError("manifest has no copyable starter/reference code")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", required=True, help="course slug, for example c-programming")
    parser.add_argument("--source", help="course-relative source path; defaults to the first code entry in practice-bundle.json")
    parser.add_argument("--name", help="target directory name under .practice/<course>/")
    args = parser.parse_args()

    try:
        source = select_source(args.course, args.source)
    except (ValueError, json.JSONDecodeError) as exc:
        return fail(str(exc))

    target_root = PRACTICE / args.course
    target_name = args.name or source.name
    target_component = Path(target_name)
    if (
        target_component.is_absolute()
        or len(target_component.parts) != 1
        or target_component.name in {"", ".", ".."}
        or target_component.name != target_name
    ):
        return fail("--name must be one safe directory name, not an absolute or nested path")
    target = target_root / target_name
    if not ignored(target_root):
        return fail(f"{target_root.relative_to(ROOT)} is not ignored; fix .gitignore before copying")
    if target.exists():
        return fail(f"target already exists: {target.relative_to(ROOT)}; existing work was not overwritten")

    target_root.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        shutil.copytree(source, target)
    else:
        target.mkdir(parents=True)
        shutil.copy2(source, target / source.name)

    if not ignored(target):
        return fail(f"copied target is unexpectedly visible to Git: {target.relative_to(ROOT)}")

    print(f"Created personal practice copy: {target.relative_to(ROOT)}")
    print(f"Edit only this copy, not {source.relative_to(ROOT)}")
    print(f"Verify: git check-ignore -v {target.relative_to(ROOT)}")
    print("Verify main repository remains clean: git status --short --untracked-files=all")
    print("Warning: do not run 'git clean -fdx' at the repository root; it can delete .practice/. ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
