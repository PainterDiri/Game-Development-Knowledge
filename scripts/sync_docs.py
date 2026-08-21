#!/usr/bin/env python3
"""Sync public source Markdown into MkDocs' docs directory.

The editable source of truth stays in roadmap/, standards/, and knowledge-sets/.
This script builds browsable mirrors under docs/ while deliberately excluding
private learner state, code/build artifacts, and non-Markdown course assets.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
COURSE_SOURCE = ROOT / "knowledge-sets"
ROADMAP_SOURCE = ROOT / "roadmap"
STANDARDS_SOURCE = ROOT / "standards"
COURSE_DOCS = DOCS / "courses"
ROADMAP_DOCS = DOCS / "roadmap"
STANDARDS_DOCS = DOCS / "standards"


def copy_markdown_tree(source: Path, destination: Path) -> None:
    """Replace destination with a Markdown-only mirror of source."""
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for src in source.rglob("*.md"):
        if any(part.startswith(".") for part in src.relative_to(source).parts):
            continue
        rel = src.relative_to(source)
        dst = destination / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def build_course_index(courses: list[dict]) -> str:
    rows = []
    for course in courses:
        rows.append(
            f"| {course['order']} | {course['title']} | {course['depth']} | "
            f"{course['phase']} | {course['practice']} | `{course['status']}` | "
            f"[打开课程](../courses/{course['slug']}/README.md) |"
        )
    return "\n".join(
        [
            "# 课程索引",
            "",
            "本页由 `python3 scripts/sync_docs.py` 根据课程元数据自动生成。",
            "课程正文的源文件位于仓库根目录 `knowledge-sets/`。",
            "这里的状态表示公开课程材料的生成状态，不代表任何学习者的个人进度。",
            "",
            "| 顺序 | 课程 | 深度 | 阶段 | 实践 | 公开内容状态 | 文档 |",
            "|---:|---|---:|---:|---|---|---|",
            *rows,
            "",
        ]
    )


def main() -> int:
    index = json.loads((ROOT / "roadmap/course-index.json").read_text(encoding="utf-8"))

    copy_markdown_tree(COURSE_SOURCE, COURSE_DOCS)
    copy_markdown_tree(ROADMAP_SOURCE, ROADMAP_DOCS)
    copy_markdown_tree(STANDARDS_SOURCE, STANDARDS_DOCS)

    # The public course landing page links to Markdown, not the JSON metadata file.
    course_landing = COURSE_DOCS / "README.md"
    if course_landing.exists():
        text = course_landing.read_text(encoding="utf-8")
        text = text.replace("../roadmap/course-index.json", "../roadmap/course-index.md")
        course_landing.write_text(text, encoding="utf-8")

    generated_index = build_course_index(index["courses"])
    (ROADMAP_DOCS / "course-index.md").write_text(generated_index, encoding="utf-8")

    print(
        f"Synced {len(index['courses'])} courses plus public roadmap/standards "
        "Markdown into docs/"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
