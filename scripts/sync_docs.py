#!/usr/bin/env python3
"""Build the public MkDocs tree from course sources and metadata."""
from __future__ import annotations

import html
import json
import shutil
from collections import defaultdict
from pathlib import Path

from package_practice import build_bundle

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
COURSE_SOURCE = ROOT / "knowledge-sets"
ROADMAP_SOURCE = ROOT / "roadmap"
STANDARDS_SOURCE = ROOT / "standards"
COURSE_DOCS = DOCS / "courses"
ROADMAP_DOCS = DOCS / "roadmap"
STANDARDS_DOCS = DOCS / "standards"
DOWNLOADS_DOCS = DOCS / "downloads"

PHASE_NAMES = {
    0: "工具链",
    1: "编程与数学",
    2: "算法与程序设计",
    3: "系统与工程",
    4: "数据与网络",
    5: "图形与媒体",
    6: "语言、AI 与引擎",
    7: "Unity 肉鸽",
    8: "UE、在线与优化",
    9: "发行",
}
STATUS_LABELS = {
    "planned": "已规划",
    "scaffolded": "准备中",
    "in-progress": "建设中",
    "completed": "可学习",
}
ROLE_LABELS = {
    "core": "核心主线",
    "supporting": "支撑课程",
    "specialization": "方向拓展",
}
STATUS_CLASSES = {
    "planned": "",
    "scaffolded": "",
    "in-progress": "is-building",
    "completed": "is-ready",
}
PUBLIC_SUFFIXES = {
    ".md", ".txt", ".json", ".csv", ".tsv", ".xml", ".yaml", ".yml", ".toml",
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg",
    ".py", ".c", ".h", ".cpp", ".hpp", ".cs", ".java", ".js", ".ts", ".lua", ".sql",
    ".shader", ".hlsl", ".glsl", ".compute", ".sh", ".ps1", ".cmake",
    ".unity", ".prefab", ".asset", ".meta", ".uproject", ".uplugin",
}


def is_public_source(path: Path, source: Path) -> bool:
    rel = path.relative_to(source)
    if any(part.startswith(".") or part in {"Library", "Temp", "Build", "Binaries", "Intermediate", "Saved"} for part in rel.parts):
        return False
    return path.name in {"CMakeLists.txt", "Makefile", "LICENSE", "LICENSE.md"} or path.suffix.lower() in PUBLIC_SUFFIXES


def copy_public_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True, exist_ok=True)
    for src in source.rglob("*"):
        if not src.is_file() or not is_public_source(src, source):
            continue
        dst = destination / src.relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def course_landing(course: dict) -> str:
    status = course["status"]
    label = STATUS_LABELS.get(status, status)
    css_class = STATUS_CLASSES.get(status, "")
    return f"""# {course['title']}

<div class="course-meta">
<span class="course-badge">阶段 {course['phase']} · {PHASE_NAMES.get(course['phase'], '')}</span>
<span class="course-badge">深度 {course['depth']}</span>
<span class="course-badge">实践 {course['practice']}</span>
<span class="course-badge">{ROLE_LABELS.get(course.get("curriculumRole"), course.get("curriculumRole", "未分层"))}</span>
<span class="course-badge {css_class}">{label}</span>
</div>

{course['summary']}

## 学习入口与依赖

- **前置课程**：{', '.join(f'`{item}`' for item in course.get('prerequisites', [])) or '无硬性前置；仍应按课程顺序完成补桥诊断'}
- **教学弧**：{course.get('teachingArc') or '生成正文前必须先补齐概念依赖图'}
- **预计正文规模**：{course.get('expectedLessonScale') or '生成正文前必须先确定'}

## 实践接缝

- **轨道**：`{course['practiceTrack']}`
- **集成方式**：`{course['integrationMode']}`
- **主项目切片**：{course['projectSlice']}
- **毕业项目关系**：{"必修" if course.get("capstoneRequired") else "可延后；不阻塞基础纵切片"}
- **交付优先级**：P{course.get("deliveryPriority", "?")}（P1 先做，P3 可在主线稳定后再做）

## 学完后的可验证出口

{course['outcome']}

!!! info "课程内容正在准备"
    这门课目前只有课程定位，尚未发布完整正文。生成时会先研究可靠来源并设计课程专属结构，不会把统一模板批量填满。

[返回课程总览](../../course-index.md){{ .md-button .md-button--primary }}
[查看完整路线](../../roadmap.md){{ .md-button }}
"""


def sync_bundles(courses: list[dict]) -> set[str]:
    """Generate ignored code-download archives for published courses with manifests."""
    if DOWNLOADS_DOCS.exists():
        shutil.rmtree(DOWNLOADS_DOCS)
    DOWNLOADS_DOCS.mkdir(parents=True)
    bundled: set[str] = set()
    for course in courses:
        if course["status"] != "completed":
            continue
        manifest = COURSE_SOURCE / course["slug"] / "practice-bundle.json"
        if not manifest.is_file():
            continue
        output = DOWNLOADS_DOCS / f"{course['slug']}-code.zip"
        build_bundle(course["slug"], output)
        bundled.add(course["slug"])
    (DOWNLOADS_DOCS / "README.md").write_text(downloads_landing(courses, bundled), encoding="utf-8")
    return bundled


def downloads_landing(courses: list[dict], bundled: set[str]) -> str:
    lines = [
        "# 实践代码下载",
        "",
        "本页集中列出网站已经发布的实践代码下载。课程正文、实践题面、提示、答案和验收说明仍以课程页面为准；ZIP 只承载可运行代码、测试、fixture、配置和主项目接入契约。",
        "",
        "## 下载规则",
        "",
        "- 下载包由课程目录中的 `practice-bundle.json` 显式白名单生成，不会自动收集未审查文件；",
        "- 包内不含 `Library/`、`DerivedDataCache/`、`dist/`、个人 `.practice/`、日志、密钥或用户绝对路径；",
        "- `completed` 课程才会显示正式下载入口；尚未完成的课程不会发布空包或伪造代码；",
        "- 参考代码不是唯一答案；请先完成网站题面，再用下载内容运行、对照或复制。",
        "",
        "## 当前可下载内容",
        "",
        "| 课程 | 下载 | 说明 |",
        "|---|---|---|",
    ]
    for course in sorted(courses, key=lambda item: item["order"]):
        if course["slug"] not in bundled:
            continue
        lines.append(
            f"| [{course['title']}](../courses/{course['slug']}/README.md) | "
            f"[下载 `{course['slug']}-code.zip`]({course['slug']}-code.zip) | "
            f"{course['projectSlice']} |"
        )
    if not bundled:
        lines.extend(["| 暂无 | — | 下一门完成课程通过代码包门禁后会出现在这里。 |"] )
    lines.extend(["", "## 对课程作者的约束", "", "每门课程最多提供一个主实践和两个微实验。没有独立代码价值的课程也可以下载数据、fixture、脚本或参考输入，但不能为了有 ZIP 而强行塞入 Unity 工程。", ""])
    return "\n".join(lines)


def append_bundle_link(destination: Path, course: dict, bundled: set[str]) -> None:
    if course["slug"] not in bundled:
        return
    readme = destination / "README.md"
    if not readme.is_file():
        return
    marker = "<!-- practice-bundle-link -->"
    text = readme.read_text(encoding="utf-8")
    if marker in text:
        text = text.split(marker, 1)[0].rstrip()
    text += (
        f"\n\n{marker}\n\n"
        "## 下载实践代码\n\n"
        "学习内容仍在本页及课程实践页中；下载包只包含经过白名单审核的可运行代码、测试、配置和主项目接入契约。"
        f"\n\n[下载 `{course['slug']}-code.zip`](../../downloads/{course['slug']}-code.zip) · "
        "[查看全部实践代码下载](../../downloads/README.md)"
        "\n"
    )
    readme.write_text(text, encoding="utf-8")


def sync_courses(courses: list[dict], bundled: set[str]) -> None:
    if COURSE_DOCS.exists():
        shutil.rmtree(COURSE_DOCS)
    COURSE_DOCS.mkdir(parents=True)

    for course in courses:
        source = COURSE_SOURCE / course["slug"]
        destination = COURSE_DOCS / course["slug"]
        if course["status"] in {"planned", "scaffolded"}:
            destination.mkdir(parents=True)
            (destination / "README.md").write_text(course_landing(course), encoding="utf-8")
        else:
            copy_public_tree(source, destination)
            append_bundle_link(destination, course, bundled)


def build_course_catalog(courses: list[dict]) -> str:
    grouped: dict[int, list[dict]] = defaultdict(list)
    for course in courses:
        grouped[course["phase"]].append(course)

    lines = [
        "# 课程总览",
        "",
        "从阶段 0 开始按顺序推进；也可以按当前项目问题跳转，但应先检查课程首页中的前置。状态只表示公开内容是否已经生成，不代表任何学习者的进度。",
        "",
        "```mermaid",
        "flowchart TB",
        "    subgraph Core[基础与系统]",
        "        direction LR",
        "        P0[0 工具链] --> P1[1 编程与数学] --> P2[2 算法与设计] --> P3[3 系统与工程] --> P4[4 数据与网络]",
        "    end",
        "    subgraph Game[游戏工程与交付]",
        "        direction LR",
        "        P5[5 图形与媒体] --> P6[6 AI 与引擎] --> P7[7 Unity 肉鸽] --> P8[8 UE / 在线 / 优化] --> P9[9 发行]",
        "    end",
        "    P4 --> P5",
        "```",
        "",
    ]
    for phase in sorted(grouped):
        lines.extend([f"## 阶段 {phase} · {PHASE_NAMES.get(phase, '')}", "", '<div class="grid cards" markdown>', ""])
        for course in sorted(grouped[phase], key=lambda item: item["order"]):
            label = STATUS_LABELS.get(course["status"], course["status"])
            css_class = STATUS_CLASSES.get(course["status"], "")
            lines.extend([
                f"-   :material-book-open-page-variant-outline: **[{course['shortTitle']}](courses/{course['slug']}/README.md)**",
                "",
                f"    <span class=\"course-badge\">{course['depth']}</span> <span class=\"course-badge\">{html.escape(str(course['practice']))}</span> <span class=\"course-badge\">{html.escape(ROLE_LABELS.get(course.get('curriculumRole'), course.get('curriculumRole', '未分层')))}</span> <span class=\"course-badge {css_class}\">{label}</span>",
                "",
                f"    {course['summary']}",
                "",
                f"    <span class=\"course-outcome\"><strong>出口：</strong>{course['outcome']}</span>",
                "",
                f"    <span class=\"course-outcome\"><strong>接缝：</strong>`{course['practiceTrack']}` · `{course['integrationMode']}` · {html.escape(course['projectSlice'])}</span>",
                "",
                f"    <span class=\"course-outcome\"><strong>路线：</strong>{'毕业项目必修' if course.get('capstoneRequired') else ROLE_LABELS.get(course.get('curriculumRole'), '可延后') + '，不阻塞基础纵切片'}</span>",
                "",
            ])
        lines.extend(["</div>", ""])
    return "\n".join(lines)


def build_metadata_index(courses: list[dict]) -> str:
    return "\n".join([
        "# 课程元数据索引",
        "",
        "本页供维护流程核对顺序、深度、阶段、实践接口和公开内容状态。普通学习请使用网站的课程总览。",
        "",
        "| 顺序 | 课程 | 深度 | 阶段 | 路线角色 | 毕业必修 | 实践 | 接缝轨道 | 集成方式 | 主项目切片 | 状态 |",
        "|---:|---|---:|---:|---|---|---|---|---|---|---|",
        *[
            f"| {c['order']} | {c['title']} | {c['depth']} | {c['phase']} | {ROLE_LABELS.get(c.get('curriculumRole'), c.get('curriculumRole', '未分层'))} | {'是' if c.get('capstoneRequired') else '否'} | {c['practice']} | `{c['practiceTrack']}` | `{c['integrationMode']}` | {c['projectSlice']} | `{c['status']}` |"
            for c in courses
        ],
        "",
    ])


def main() -> int:
    index = json.loads((ROOT / "roadmap/course-index.json").read_text(encoding="utf-8"))
    courses = index["courses"]

    (ROADMAP_SOURCE / "course-index.md").write_text(build_metadata_index(courses), encoding="utf-8")
    copy_public_tree(ROADMAP_SOURCE, ROADMAP_DOCS)
    copy_public_tree(STANDARDS_SOURCE, STANDARDS_DOCS)
    bundled = sync_bundles(courses)
    sync_courses(courses, bundled)
    (DOCS / "course-index.md").write_text(build_course_catalog(courses), encoding="utf-8")

    print(f"Synced {len(courses)} courses; generated {len(bundled)} practice bundle(s); scaffolded courses publish concise landing pages only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
