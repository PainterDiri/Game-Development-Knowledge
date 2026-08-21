#!/usr/bin/env python3
"""Lightweight repository checks; intentionally dependency-free."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "AGENTS.md",
    "README.md",
    "mkdocs.yml",
    "requirements.txt",
    ".github/workflows/pages.yml",
    "docs/automatic-progress.md",
    "docs/javascripts/learning-progress.js",
    "docs/stylesheets/learning-progress.css",
    "roadmap/README.md",
    "roadmap/curriculum-mapping.md",
    "roadmap/practice-system.md",
    "roadmap/course-index.json",
    "standards/README.md",
    "standards/knowledge-generation-spec.md",
    "standards/generation-workflow.md",
    "standards/course-folder-template.md",
    "standards/research-and-citation.md",
    "standards/practice-design.md",
    "standards/naming-and-architecture.md",
    "standards/quality-gates.md",
    "standards/ai-course-prompt.md",
    "knowledge-sets/README.md",
]
COURSE_FILES = [
    "README.md",
    "lessons/00-course-map.md",
    "labs/README.md",
    "labs/solutions.md",
    "assessments/questions.md",
    "assessments/answers.md",
    "assessments/rubric.md",
    "notes/glossary.md",
    "references/research-notes.md",
    "references/bibliography.md",
]
FORBIDDEN_PUBLIC_STATE = [
    "progress.md",
    "exercise-log.md",
    "mistakes.md",
    "decision-log.md",
    "workspace",
    "notes/exercise-log.md",
    "notes/mistakes.md",
    "notes/decision-log.md",
]
SKIP_PARTS = {".git", ".venv", ".practice", "site"}
PRIVATE_PATH_RE = re.compile(r"/(?:Users|home)/[^/\s`]+/")
SECRET_RES = [
    re.compile(r"\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----"),
]
QUESTION_ID_RE = re.compile(r"^###\s+((?:[A-Z][A-Z0-9-]*-)?Q\d+|综合题)\s*[：:]", re.MULTILINE)
COMPLETION_MARKERS = ("待课程生成时填写", "待研究后填写", "待设计", "[ ] 待定义")


def is_public_path(path: Path) -> bool:
    return not any(part in SKIP_PARTS for part in path.parts)


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            errors.append(f"missing required file: {rel}")

    try:
        index = json.loads((ROOT / "roadmap/course-index.json").read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"cannot read course-index.json: {exc}")
        index = {"courses": []}

    slugs: set[str] = set()
    orders: list[int] = []
    for course in index.get("courses", []):
        slug = course.get("slug", "")
        if not slug or slug in slugs:
            errors.append(f"duplicate or empty course slug: {slug!r}")
        slugs.add(slug)
        orders.append(course.get("order"))
        base = ROOT / "knowledge-sets" / slug

        for rel in COURSE_FILES:
            if not (base / rel).exists():
                errors.append(f"{slug}: missing {rel}")
        for rel in FORBIDDEN_PUBLIC_STATE:
            if (base / rel).exists():
                errors.append(f"{slug}: learner state must not be public: {rel}")

        questions_path = base / "assessments/questions.md"
        answers_path = base / "assessments/answers.md"
        solutions_path = base / "labs/solutions.md"
        if questions_path.exists() and answers_path.exists():
            question_ids = set(QUESTION_ID_RE.findall(questions_path.read_text(encoding="utf-8")))
            answer_text = answers_path.read_text(encoding="utf-8")
            missing_answers = sorted(qid for qid in question_ids if qid not in answer_text)
            if missing_answers:
                errors.append(f"{slug}: answer file missing IDs: {', '.join(missing_answers)}")
            if "<details>" not in answer_text:
                errors.append(f"{slug}: assessments/answers.md must use <details> blocks")
        if solutions_path.exists() and "<details>" not in solutions_path.read_text(encoding="utf-8"):
            errors.append(f"{slug}: labs/solutions.md must use <details> blocks")

        if course.get("status") == "completed":
            for rel in COURSE_FILES:
                path = base / rel
                if not path.exists():
                    continue
                text = path.read_text(encoding="utf-8")
                markers = [marker for marker in COMPLETION_MARKERS if marker in text]
                if markers:
                    errors.append(
                        f"{slug}: completed course still contains scaffold marker(s) in {rel}: "
                        + ", ".join(markers)
                    )

    if orders != sorted(orders):
        errors.append("course orders are not monotonic")

    # Check local Markdown links, ignoring URLs, anchors, and template placeholders.
    link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for md in ROOT.rglob("*.md"):
        if not is_public_path(md):
            continue
        text = md.read_text(encoding="utf-8")
        if PRIVATE_PATH_RE.search(text):
            errors.append(f"{md.relative_to(ROOT)}: contains a private absolute path")
        for secret_re in SECRET_RES:
            if secret_re.search(text):
                errors.append(f"{md.relative_to(ROOT)}: contains a possible secret")
        for target in link_re.findall(text):
            target = target.split("#", 1)[0].strip()
            if (
                not target
                or target in {"URL", "slug", "course-slug"}
                or "://" in target
                or target.startswith("mailto:")
                or "<" in target
            ):
                continue
            candidate = (md.parent / target).resolve()
            if not candidate.exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link -> {target}")

    mkdocs_path = ROOT / "mkdocs.yml"
    if mkdocs_path.exists():
        mkdocs_text = mkdocs_path.read_text(encoding="utf-8")
        for asset in (
            "javascripts/learning-progress.js",
            "stylesheets/learning-progress.css",
        ):
            if asset not in mkdocs_text:
                errors.append(f"mkdocs.yml does not load automatic-resume asset: {asset}")

    if errors:
        print("CHECK FAILED")
        print("\n".join(f"- {error}" for error in errors))
        return 1

    print(
        f"CHECK OK: {len(index.get('courses', []))} course scaffolds, "
        "public content, answer files, automatic-resume assets and local links valid"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
