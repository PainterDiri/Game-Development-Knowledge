import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_repo


class PrerequisiteTests(unittest.TestCase):
    def check(self, courses):
        errors = []
        check_repo.check_prerequisites(errors, courses)
        return errors

    def test_valid_dag(self):
        self.assertEqual(self.check([{"slug": "a", "order": 0, "prerequisites": []},
                                    {"slug": "b", "order": 1, "prerequisites": ["a"]}]), [])

    def test_unknown_cycle_self_duplicate_and_bad_order(self):
        cases = [
            [{"slug": "a", "order": 0, "prerequisites": ["missing"]}],
            [{"slug": "a", "order": 0, "prerequisites": ["a"]}],
            [{"slug": "a", "order": 0, "prerequisites": ["b"]}, {"slug": "b", "order": 1, "prerequisites": ["a"]}],
            [{"slug": "a", "order": 0, "prerequisites": []}, {"slug": "b", "order": 0, "prerequisites": []}],
            [{"slug": "a", "order": "0", "prerequisites": []}],
            [{"slug": "a", "order": 0, "prerequisites": "b"}],
            [{"slug": "a", "order": 0, "prerequisites": []},
             {"slug": "b", "order": 1, "prerequisites": ["a", "a"]}],
        ]
        for courses in cases:
            with self.subTest(courses=courses):
                self.assertTrue(self.check(courses))


class PortablePathTests(unittest.TestCase):
    def test_accepts_portable_relative_paths(self):
        self.assertTrue(check_repo.is_portable_relative_path("code/runtime-kit"))
        self.assertTrue(check_repo.is_portable_relative_path("runtime-kit", single_component=True))

    def test_rejects_escape_windows_and_nested_bundle_names(self):
        for value in ["../escape", r"..\\escape", r"C:\\escape", "bad:name", "trailing."]:
            with self.subTest(value=value):
                self.assertFalse(check_repo.is_portable_relative_path(value))
        self.assertFalse(check_repo.is_portable_relative_path("nested/name", single_component=True))


class ExerciseTests(unittest.TestCase):
    def check_lesson(self, text):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "README.md").write_text("course", encoding="utf-8")
            (base / "practice.md").write_text(
                "最小版本 分阶段 验收 常见失败 Git 隔离 init_practice.py git check-ignore git status",
                encoding="utf-8",
            )
            (base / "lessons").mkdir()
            (base / "lessons/01.md").write_text(text, encoding="utf-8")
            errors = []
            with contextlib.redirect_stdout(io.StringIO()):
                check_repo.check_course_structure(errors, "test", "completed", base)
            return errors

    @staticmethod
    def valid_question(question_id="C01-Q1"):
        return (
            f"## 本章练习\n\n### {question_id}：a\n\n"
            "**题型**：代码追踪  \n"
            "**作答产物**：状态表与最终结论。\n\n"
            "给定输入后写出结果。\n\n"
            "<details><summary>讲解、判定与验证</summary>推理正文、边界、验证与游戏映射。</details>\n"
        )

    def test_duplicate_id_within_one_lesson(self):
        text = self.valid_question() + self.valid_question()
        errors = self.check_lesson(text)
        self.assertTrue(any("duplicate question IDs" in error for error in errors))

    def test_hint_block_is_forbidden(self):
        text = self.valid_question().replace(
            "<details><summary>讲解、判定与验证</summary>",
            "<details><summary>最小提示</summary>先想一想。</details>\n"
            "<details><summary>讲解、判定与验证</summary>",
        )
        self.assertTrue(any("must not contain hint" in error for error in self.check_lesson(text)))

    def test_question_requires_type_and_deliverable(self):
        for marker in ["**题型**：代码追踪  \n", "**作答产物**：状态表与最终结论。\n"]:
            text = self.valid_question().replace(marker, "")
            self.assertTrue(any("metadata" in error for error in self.check_lesson(text)))

    def test_answer_must_use_complete_named_block(self):
        for replacement in [
            "<details><summary>讲解</summary></details>",
            "<details><summary>答案</summary>只有结论。</details>",
            "<details><summary>讲解、判定与验证</summary>未闭合",
        ]:
            text = self.valid_question()
            text = text[:text.index("<details>")] + replacement
            self.assertTrue(any("missing a complete" in error for error in self.check_lesson(text)))

    def test_valid_question_without_hint(self):
        errors = self.check_lesson(self.valid_question())
        self.assertFalse(any("exercise C01-Q1" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
