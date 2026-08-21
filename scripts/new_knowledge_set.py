#!/usr/bin/env python3
"""Create a course knowledge-set scaffold from the repository contract."""
from __future__ import annotations
import argparse, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def slugify(value: str) -> str:
    value = value.strip().lower().replace(' ', '-')
    value = re.sub(r'[^a-z0-9\u4e00-\u9fff_-]+', '-', value)
    return re.sub(r'-+', '-', value).strip('-')

def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--course', required=True, help='course slug')
    p.add_argument('--title', help='course title; defaults to metadata or slug')
    p.add_argument('--source', default='增补')
    p.add_argument('--depth', default='D2')
    p.add_argument('--phase', default='待定')
    p.add_argument('--practice', default='待定')
    p.add_argument('--status', default='scaffolded')
    args = p.parse_args()
    slug = slugify(args.course)
    index_path = ROOT / 'roadmap/course-index.json'
    data = json.loads(index_path.read_text(encoding='utf-8'))
    existing = next((c for c in data['courses'] if c['slug'] == slug), None)
    title = args.title or (existing or {}).get('title') or slug
    source = (existing or {}).get('source', args.source)
    depth = (existing or {}).get('depth', args.depth)
    phase = (existing or {}).get('phase', args.phase)
    practice = (existing or {}).get('practice', args.practice)
    base = ROOT / 'knowledge-sets' / slug
    dirs = ['lessons', 'labs', 'assessments', 'code', 'notes', 'references', 'assets']
    for d in dirs:
        (base / d).mkdir(parents=True, exist_ok=True)
    write(base / 'README.md', f"""# {title}

- 课程 ID：`{slug}`
- 来源：{source}
- 目标深度：**{depth}**
- 所属阶段：{phase}
- 挂接实践：`{practice}`
- 状态：`{args.status}`

## 这门课要解决的游戏开发问题

待研究后填写。

## 出口能力

- 待定义：能够解释机制、验证实现并映射到实际游戏问题。

## 章节导航

- [课程地图](lessons/00-course-map.md)
- [实验入口](labs/README.md)
- [实践提示与参考解法](labs/solutions.md)
- [题目](assessments/questions.md)
- [答案与解析](assessments/answers.md)
- [评分标准](assessments/rubric.md)
- [术语表](notes/glossary.md)
- 阅读位置由网站在当前浏览器自动保存，无需手工维护进度文件。
- [研究笔记](references/research-notes.md)

## 环境与版本

待研究后填写。

## 完成标准

公开课程包含题目、折叠答案、解析和实践参考解法；不要求个人作答、错题或进度文档。
""")
    write(base / 'lessons/00-course-map.md', '# 课程地图\n\n先研究、再规划章节。\n')
    write(base / 'labs/README.md', '# 实验入口\n\n最多 1 个主实践 + 2 个微实验。个人实现可放任意位置；如放在本仓库，按需使用被忽略的 `.practice/{}/`。\n'.format(slug))
    write(base / 'labs/solutions.md', '# 实践提示与参考解法\n\n> 请先独立完成实验；卡住时按需展开。\n\n<details>\n<summary>最小提示</summary>\n\n待课程生成时填写。\n\n</details>\n\n<details>\n<summary>参考路线、验证与常见失败</summary>\n\n待课程生成时填写；包含关键不变量、参考方案、验证命令、预期结果、常见失败和替代方案。\n\n</details>\n')
    write(base / 'assessments/questions.md', '# 章节题目\n\n待课程生成时填写。\n')
    write(base / 'assessments/answers.md', '# 题目答案与解析\n\n待课程生成时填写；使用折叠块隐藏解析。\n')
    write(base / 'assessments/rubric.md', '# 题目评分标准\n\n待课程生成时填写。\n')
    write(base / 'notes/glossary.md', '# 术语表\n')
    write(base / 'references/research-notes.md', '# 研究笔记\n')
    write(base / 'references/bibliography.md', '# 参考书目\n')
    for d in ['code', 'assets']:
        (base / d / '.gitkeep').touch(exist_ok=True)
    if not existing:
        next_order = max((c['order'] for c in data['courses']), default=-1) + 1
        data['courses'].append({'order': next_order, 'slug': slug, 'title': title, 'source': source, 'depth': depth, 'phase': phase, 'practice': practice, 'status': args.status})
        index_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'created {base.relative_to(ROOT)}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
