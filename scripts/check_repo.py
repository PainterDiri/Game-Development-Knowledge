#!/usr/bin/env python3
"""Dependency-free repository checks for public course content."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md", "README.md", "mkdocs.yml", "requirements.txt", ".github/workflows/pages.yml",
    "docs/automatic-progress.md", "docs/javascripts/learning-progress.js",
    "docs/javascripts/learning-ui.js", "docs/stylesheets/learning-progress.css", "docs/stylesheets/site.css",
    "roadmap/README.md", "roadmap/curriculum-mapping.md", "roadmap/practice-system.md",
    "roadmap/course-index.json", "standards/README.md", "standards/knowledge-generation-spec.md",
    "standards/generation-workflow.md", "standards/course-folder-template.md",
    "standards/research-and-citation.md", "standards/practice-design.md",
    "standards/naming-and-architecture.md", "standards/quality-gates.md",
    "standards/ai-course-prompt.md", "knowledge-sets/README.md", "scripts/init_practice.py",
]
# Legacy map files remain accepted only for historical scaffolds. README.md is the
# sole course landing page and course map for new and completed courses.
SCAFFOLD_FILES = ["README.md"]
FORBIDDEN_PUBLIC_STATE = {
    "progress.md", "exercise-log.md", "mistakes.md", "decision-log.md", "workspace"
}
SKIP_PARTS = {".git", ".venv", ".practice", "site", "__pycache__"}
PRIVATE_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s`]+/")
SECRET_RES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]
QUESTION_ID_RE = re.compile(r"^###\s+((?:[A-Z][A-Z0-9-]*-)?Q\d+|综合题)\s*[：:]", re.MULTILINE)
COMPLETION_MARKERS = ("待课程生成时填写", "待研究后填写", "待设计", "待定义")
VALID_STATUSES = {"planned", "scaffolded", "in-progress", "completed"}
VALID_CURRICULUM_ROLES = {"core", "supporting", "specialization"}
MIN_LESSON_CHARS = 1800
MIN_LESSON_HEADINGS = 3
QUALITY_SIGNALS = {
    "mechanism": ("机制", "不变量", "定义与边界"),
    "example": ("示例", "```", "命令"),
    "verification": ("验证", "验收", "预期结果"),
    "failure": ("失败", "边界", "常见错误"),
    "mapping": ("Unity", "Unreal", "游戏映射"),
}


def is_public_path(path: Path) -> bool:
    return not any(part in SKIP_PARTS for part in path.parts)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def check_course_structure(errors: list[str], slug: str, status: str, base: Path) -> None:
    for rel in SCAFFOLD_FILES:
        if not (base / rel).exists():
            errors.append(f"{slug}: missing {rel} for status {status}")

    forbidden = [
        base / "assessments.md",
        base / "assessments",
        base / "references",
        base / "integration-contract.md",
    ]
    for path in forbidden:
        if path.exists():
            errors.append(f"{slug}: obsolete standalone course artifact must be removed: {path.relative_to(base)}")

    practice_path = base / "practice.md"
    bundle_manifest = base / "practice-bundle.json"
    if practice_path.exists():
        practice_text = read_text(practice_path)
        for marker in ("最小版本", "分阶段", "验收", "常见失败", "Git 隔离", "init_practice.py", "git check-ignore", "git status"):
            if marker not in practice_text:
                errors.append(f"{slug}: practice.md missing required self-study/safety marker: {marker}")
    elif status == "completed":
        errors.append(f"{slug}: completed course needs one practice.md")

    if (base / "code").exists() and status in {"in-progress", "completed"} and not bundle_manifest.exists():
        errors.append(f"{slug}: public code needs practice-bundle.json")

    if bundle_manifest.exists():
        try:
            bundle = json.loads(read_text(bundle_manifest))
            if bundle.get("schema") != 2 or bundle.get("slug") != slug:
                errors.append(f"{slug}: practice-bundle.json must declare schema 2 and matching slug")
            if bundle.get("downloadType") != "practice-code":
                errors.append(f"{slug}: practice-bundle.json must declare downloadType practice-code")
            includes = bundle.get("include", [])
            if not includes:
                errors.append(f"{slug}: practice-bundle.json include must not be empty")
            allowed_roles = {"code", "starter-code", "reference-code", "test-fixture", "supporting-material", "license"}
            for item in includes:
                if not isinstance(item, dict) or not item.get("path") or not item.get("role"):
                    errors.append(f"{slug}: every bundle include needs path and role")
                elif item["role"] not in allowed_roles:
                    errors.append(f"{slug}: unsupported bundle role {item['role']!r}")
                elif ".." in Path(item["path"]).parts or Path(item["path"]).is_absolute():
                    errors.append(f"{slug}: bundle path escapes course: {item['path']!r}")
                elif not (base / item["path"]).exists():
                    errors.append(f"{slug}: bundle input missing: {item['path']}")
        except (json.JSONDecodeError, OSError) as exc:
            errors.append(f"{slug}: invalid practice-bundle.json: {exc}")

    lessons_dir = base / "lessons"
    legacy_map = lessons_dir / "00-course-map.md"
    lesson_files = sorted(path for path in lessons_dir.glob("*.md") if path.name != "00-course-map.md") if lessons_dir.exists() else []
    if status == "completed":
        if legacy_map.exists():
            errors.append(f"{slug}: completed course must not keep lessons/00-course-map.md")
        if not lesson_files:
            errors.append(f"{slug}: completed course needs detailed lesson files")

    seen_questions: set[str] = set()
    for lesson in lesson_files:
        text = read_text(lesson)
        ids = QUESTION_ID_RE.findall(text)
        duplicates = sorted(qid for qid in ids if qid in seen_questions)
        if duplicates:
            errors.append(f"{slug}: duplicate question IDs in {lesson.name}: {', '.join(duplicates)}")
        seen_questions.update(ids)
        if status == "completed":
            if len(text) < MIN_LESSON_CHARS:
                errors.append(f"{slug}: {lesson.name} is too thin for a completed lesson ({len(text)} chars; needs at least {MIN_LESSON_CHARS})")
            if len(re.findall(r"^##\s+", text, re.MULTILINE)) < MIN_LESSON_HEADINGS:
                errors.append(f"{slug}: {lesson.name} needs several substantive sections, not just a title and exercise")
            if "## 本章练习" not in text:
                errors.append(f"{slug}: {lesson.name} missing chapter-end exercise section")
            if len(ids) < 2:
                errors.append(f"{slug}: {lesson.name} needs at least two representative exercises")
            if text.count("<details>") < len(ids) * 2:
                errors.append(f"{slug}: {lesson.name} needs a hint and explanation details block for every exercise")
            missing_signals = [name for name, tokens in QUALITY_SIGNALS.items() if not any(token in text for token in tokens)]
            if missing_signals:
                errors.append(f"{slug}: {lesson.name} missing teaching signals: {', '.join(missing_signals)}")

    if status == "completed" and len(seen_questions) < len(lesson_files) * 2:
        errors.append(f"{slug}: completed course has too few chapter-local exercises")

    if status == "completed":
        for path in base.rglob("*.md"):
            markers = [m for m in COMPLETION_MARKERS if m in read_text(path)]
            if markers:
                errors.append(f"{slug}: completed file contains scaffold markers in {path.relative_to(base)}: {', '.join(markers)}")


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    try:
        index = json.loads(read_text(ROOT / "roadmap/course-index.json"))
    except Exception as exc:
        errors.append(f"cannot read course-index.json: {exc}")
        index = {"courses": []}

    slugs: set[str] = set()
    orders: list[int] = []
    statuses: Counter[str] = Counter()
    for course in index.get("courses", []):
        slug = course.get("slug", "")
        status = course.get("status", "")
        if not slug or slug in slugs:
            errors.append(f"duplicate or empty course slug: {slug!r}")
        slugs.add(slug)
        orders.append(course.get("order"))
        statuses[status] += 1
        if status not in VALID_STATUSES:
            errors.append(f"{slug}: invalid status {status!r}")
        for key in ("title", "shortTitle", "summary", "outcome", "depth", "phase", "practiceProject", "curriculumRole", "practiceRequired", "deliveryPriority"):
            if key not in course or course[key] in (None, ""):
                errors.append(f"{slug}: missing metadata field {key}")
        if course.get("curriculumRole") not in VALID_CURRICULUM_ROLES:
            errors.append(f"{slug}: invalid curriculumRole {course.get('curriculumRole')!r}")
        if not isinstance(course.get("practiceRequired"), bool):
            errors.append(f"{slug}: practiceRequired must be boolean")
        if course.get("deliveryPriority") not in {1, 2, 3}:
            errors.append(f"{slug}: deliveryPriority must be 1, 2, or 3")

        base = ROOT / "knowledge-sets" / slug
        if not base.exists():
            errors.append(f"{slug}: missing course directory")
            continue
        check_course_structure(errors, slug, status, base)
        for path in base.rglob("*"):
            if path.is_file() and path.name in FORBIDDEN_PUBLIC_STATE:
                errors.append(f"{slug}: learner state must not be public: {path.relative_to(base)}")

    if orders != sorted(orders):
        errors.append("course orders are not monotonic")

    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in ROOT.rglob("*.md"):
        if not is_public_path(md):
            continue
        text = read_text(md)
        if PRIVATE_PATH_RE.search(text):
            errors.append(f"{md.relative_to(ROOT)}: contains a private absolute path")
        for secret_re in SECRET_RES:
            if secret_re.search(text):
                errors.append(f"{md.relative_to(ROOT)}: contains a possible secret")
        for target in link_re.findall(text):
            target = target.split("#", 1)[0].strip()
            if not target or target in {"URL", "slug", "course-slug"} or "://" in target or target.startswith("mailto:") or "<" in target:
                continue
            if not (md.parent / target).resolve().exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link -> {target}")

    if (ROOT / "mkdocs.yml").exists():
        config = read_text(ROOT / "mkdocs.yml")
        for asset in (
            "javascripts/learning-progress.js", "javascripts/learning-ui.js",
            "stylesheets/learning-progress.css", "stylesheets/site.css",
        ):
            if asset not in config:
                errors.append(f"mkdocs.yml does not load required asset: {asset}")
        if "name: mermaid" not in config:
            errors.append("mkdocs.yml does not configure Mermaid")

    if errors:
        print("CHECK FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    status_summary = ", ".join(f"{key}={value}" for key, value in sorted(statuses.items()))
    published = statuses.get("completed", 0)
    scaffolded = statuses.get("planned", 0) + statuses.get("scaffolded", 0)
    print(f"CHECK OK: {len(slugs)} courses ({status_summary}); published={published}, not-yet-published={scaffolded}; structural gates, links, privacy, UI assets and state rules valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
