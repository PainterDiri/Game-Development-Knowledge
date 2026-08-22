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
    "standards/ai-course-prompt.md", "knowledge-sets/README.md",
]
SCAFFOLD_FILES = ["README.md", "lessons/00-course-map.md", "references/research-notes.md"]
COMPLETED_FILES = [
    *SCAFFOLD_FILES,
    "labs/README.md", "labs/solutions.md",
    "references/bibliography.md",
]
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
        for key in ("title", "shortTitle", "summary", "outcome", "depth", "phase", "practice"):
            if key not in course or course[key] in (None, ""):
                errors.append(f"{slug}: missing metadata field {key}")

        base = ROOT / "knowledge-sets" / slug
        required_files = COMPLETED_FILES if status == "completed" else SCAFFOLD_FILES
        for rel in required_files:
            if not (base / rel).exists():
                errors.append(f"{slug}: missing {rel} for status {status}")
        for path in base.rglob("*") if base.exists() else []:
            if path.is_file() and path.name in FORBIDDEN_PUBLIC_STATE:
                errors.append(f"{slug}: learner state must not be public: {path.relative_to(base)}")

        assessment_path = base / "assessments.md"
        questions_path = base / "assessments/questions.md"
        answers_path = base / "assessments/answers.md"
        solutions_path = base / "labs/solutions.md"
        if assessment_path.exists() and (questions_path.exists() or answers_path.exists()):
            errors.append(f"{slug}: use either assessments.md or assessments/questions.md + answers.md, not both")
        if questions_path.exists() != answers_path.exists():
            errors.append(f"{slug}: questions.md and answers.md must be created together")
        if assessment_path.exists():
            assessment_text = assessment_path.read_text(encoding="utf-8")
            question_ids = set(QUESTION_ID_RE.findall(assessment_text))
            if status == "completed" and question_ids and "<details>" not in assessment_text:
                errors.append(f"{slug}: completed assessments.md must use <details> blocks")
        elif questions_path.exists() and answers_path.exists():
            question_ids = set(QUESTION_ID_RE.findall(questions_path.read_text(encoding="utf-8")))
            answer_text = answers_path.read_text(encoding="utf-8")
            missing_answers = sorted(qid for qid in question_ids if qid not in answer_text)
            if missing_answers:
                errors.append(f"{slug}: answer file missing IDs: {', '.join(missing_answers)}")
            if status == "completed" and "<details>" not in answer_text:
                errors.append(f"{slug}: completed answers.md must use <details> blocks")
        elif status == "completed":
            errors.append(f"{slug}: completed course needs assessments.md or split questions/answers")
        if status == "completed" and solutions_path.exists() and "<details>" not in solutions_path.read_text(encoding="utf-8"):
            errors.append(f"{slug}: completed labs/solutions.md must use <details> blocks")

        if status == "completed":
            lesson_files = [p for p in (base / "lessons").glob("*.md") if p.name != "00-course-map.md"]
            if not lesson_files:
                errors.append(f"{slug}: completed course has no lesson beyond the course map")
            for rel in COMPLETED_FILES + [str(p.relative_to(base)) for p in lesson_files]:
                path = base / rel
                if path.exists():
                    markers = [m for m in COMPLETION_MARKERS if m in path.read_text(encoding="utf-8")]
                    if markers:
                        errors.append(f"{slug}: completed file contains scaffold markers in {rel}: {', '.join(markers)}")

    if orders != sorted(orders):
        errors.append("course orders are not monotonic")

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
            if not target or target in {"URL", "slug", "course-slug"} or "://" in target or target.startswith("mailto:") or "<" in target:
                continue
            if not (md.parent / target).resolve().exists():
                errors.append(f"{md.relative_to(ROOT)}: broken link -> {target}")

    if (ROOT / "mkdocs.yml").exists():
        config = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
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
    print(f"CHECK OK: {len(slugs)} courses ({status_summary}); links, privacy, UI assets and state rules valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
