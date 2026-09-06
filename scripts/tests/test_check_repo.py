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


class ExerciseTests(unittest.TestCase):
    def check_lesson(self, text):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "README.md").write_text("course", encoding="utf-8")
            (base / "lessons").mkdir()
            (base / "lessons/01.md").write_text(text, encoding="utf-8")
            errors = []
            with contextlib.redirect_stdout(io.StringIO()):
                check_repo.check_course_structure(errors, "test", "completed", base)
            return errors

    def test_duplicate_id_within_one_lesson(self):
        errors = self.check_lesson("### C01-Q1：a\n### C01-Q1：b\n")
        self.assertTrue(any("duplicate question IDs" in error for error in errors))

    def test_hint_text_cannot_impersonate_answer_summary(self):
        errors = self.check_lesson("### C01-Q1：a\n<details><summary>提示</summary>这里有答案两个字</details>\n")
        self.assertTrue(any("missing a complete explanation" in error for error in errors))

    def test_answer_must_close_and_have_content(self):
        for block in ["<details><summary>讲解</summary></details>",
                      "<details><summary>讲解</summary>未闭合",
                      "<details><summary>讲解</summary> </details><details><summary>提示</summary>后一个块不能填补空答案</details>"]:
            self.assertTrue(any("missing a complete explanation" in error for error in self.check_lesson("### C01-Q1：a\n" + block)))

    def test_valid_answer_without_hint(self):
        errors = self.check_lesson("### C01-Q1：a\n<details><summary>讲解与验证</summary>推理正文。</details>\n")
        self.assertFalse(any("missing a complete explanation" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
