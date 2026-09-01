#!/usr/bin/env python3
"""Create a minimal course skeleton with README as the sole course-map entry."""
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
        "status": "scaffolded",
        "summary": args.summary,
        "outcome": args.outcome,
        "practiceProject": "待研究后定义的课程主实践",
        "prerequisites": [],
        "teachingArc": "待研究后按可观察任务、最小术语、机制、实验、失败与综合出口设计",
        "expectedLessonScale": "完成概念依赖图后确定；D3 课程通常需要 10–20 个连续知识单元",
    }

    base = ROOT / "knowledge-sets" / slug
    if base.exists() and any(base.rglob("*")):
        raise SystemExit(f"{base.relative_to(ROOT)} already exists; refusing to overwrite it")

    base.mkdir(parents=True, exist_ok=True)
    prerequisites = course.get("prerequisites", [])
    prereq_text = "、".join(f"`{item}`" for item in prerequisites) or "无硬性前置；仍需设计零基础诊断"
    write_new(base / "README.md", f"""# {title}

- 课程 ID：`{slug}`
- 目标深度：**{course['depth']}**
- 所属阶段：{course['phase']}
- 主实践：{course.get('practiceProject', '待研究后定义')}
- 状态：`scaffolded`

{course['summary']}

## 前置与补桥（生成正文前补全）

- 前置课程：{prereq_text}
- 零基础诊断：先设计一个 10–30 分钟、能暴露缺失概念的任务；不能用术语问卷代替。
- 补桥：若诊断失败，提供最小解释和可运行微实验，再进入第 1 章。

## 为什么按这个顺序学习（生成正文前补全）

教学弧：{course.get('teachingArc', '待研究后设计')}

把教学弧改写为逐章依赖表。第 1 章必须从学习者能观察的任务或失败开始；后续每章说明上一章的产物如何成为本章输入，不得先抛出系统边界、架构口号或术语清单。

## 章节地图（研究后再创建正文文件）

预计规模：{course.get('expectedLessonScale', '完成概念依赖图后确定')}

| 顺序 | 核心问题 | 前置输入 | 本章产出 | 验证证据 | 下一章如何使用 |
|---:|---|---|---|---|---|
| 1 | 待研究 | 待诊断 | 待定义 | 待定义 | 待定义 |

> 不要批量生成空章节。研究、依赖图和证据设计完成后再按实际难点创建页面；D3 课程不得为了少页而压缩核心推导、代码和实验。

## 可验证出口

{course['outcome']}

## 本课程主实践

- 主实践：{course.get('practiceProject', '待定义')}
- 个人实践目录：`.practice/{slug}/`（生成后必须验证 Git 忽略）

下一步：先研究可靠来源并完成课程地图，再逐章编写正文和章末练习，最后设计唯一主实践；不要创建 `lessons/00-course-map.md`、独立练习页、研究笔记或参考书目。
""")
    if not existing:
        data["courses"].append(course)
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"created minimal scaffold: {base.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
