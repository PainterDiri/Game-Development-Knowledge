#!/usr/bin/env python3
"""Create a minimal course skeleton without imposing a chapter template."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    value = value.strip().lower().replace(" ", "-")
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff_-]+", "-", value)
    return re.sub(r"-+", "-", value).strip("-")


def write_new(path: Path, text: str) -> None:
    if path.exists():
        raise FileExistsError(f"refusing to overwrite existing file: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course", required=True, help="course slug")
    parser.add_argument("--title", help="course title; defaults to metadata or slug")
    parser.add_argument("--source", default="增补")
    parser.add_argument("--depth", default="D2")
    parser.add_argument("--phase", type=int, default=0)
    parser.add_argument("--practice", default="待定")
    parser.add_argument("--summary", default="待研究后明确本课程解决的核心游戏开发问题。")
    parser.add_argument("--outcome", default="待研究后定义可验证的课程出口。")
    args = parser.parse_args()

    slug = slugify(args.course)
    index_path = ROOT / "roadmap/course-index.json"
    data = json.loads(index_path.read_text(encoding="utf-8"))
    existing = next((c for c in data["courses"] if c["slug"] == slug), None)
    title = args.title or (existing or {}).get("title") or slug
    course = existing or {
        "order": max((c["order"] for c in data["courses"]), default=-1) + 1,
        "slug": slug,
        "title": title,
        "shortTitle": title,
        "source": args.source,
        "depth": args.depth,
        "phase": args.phase,
        "practice": args.practice,
        "status": "scaffolded",
        "summary": args.summary,
        "outcome": args.outcome,
    }

    base = ROOT / "knowledge-sets" / slug
    if base.exists() and any(base.rglob("*")):
        raise SystemExit(f"{base.relative_to(ROOT)} already exists; refusing to overwrite it")

    for directory in ("lessons", "references"):
        (base / directory).mkdir(parents=True, exist_ok=True)
    write_new(base / "README.md", f"""# {title}

- 课程 ID：`{slug}`
- 目标深度：**{course['depth']}**
- 所属阶段：{course['phase']}
- 挂接实践：`{course['practice']}`
- 状态：`scaffolded`

{course['summary']}

## 可验证出口

{course['outcome']}

下一步先研究来源并完成[课程地图](lessons/00-course-map.md)，再按课程难点创建实际需要的章节、题目和实践文件。
""")
    write_new(base / "lessons/00-course-map.md", f"""# {title} · 课程地图

课程地图尚未设计。研究时先确定本课程适合推导、实现、测量、诊断、架构比较还是引擎观察，避免套用统一章节结构。
""")
    write_new(base / "references/research-notes.md", "# 研究笔记\n\n按问题记录来源、版本、关键事实、用途、限制和冲突。\n")
    if not existing:
        data["courses"].append(course)
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"created minimal scaffold: {base.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
