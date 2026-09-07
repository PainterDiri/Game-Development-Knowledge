import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import package_practice


class PackagePracticeTests(unittest.TestCase):
    def make_course(self, root: Path, manifest_overrides=None):
        course = root / "demo"
        source = course / "code" / "game"
        source.mkdir(parents=True)
        (source / "main.py").write_text("print('ok')\n", encoding="utf-8")
        (source / "README.md").write_text("baseline\n", encoding="utf-8")
        manifest = {
            "schema": 2,
            "downloadType": "practice-code",
            "slug": "demo",
            "title": "Demo",
            "bundleName": "demo-practice",
            "quickStart": ["cd workspace/game", "python3 main.py"],
            "include": [
                {"path": "code/game", "role": "editable-baseline", "target": "game"},
                {"path": "code/game", "role": "reference-code", "target": "game"},
            ],
        }
        if manifest_overrides:
            manifest.update(manifest_overrides)
        (course / "practice-bundle.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        return course

    def build(self, courses: Path, output: Path):
        with mock.patch.object(package_practice, "COURSES", courses):
            return package_practice.build_bundle("demo", output)

    def test_bundle_has_start_workspace_reference_and_safe_members(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            courses = root / "knowledge-sets"
            courses.mkdir()
            self.make_course(courses)
            output = root / "demo.zip"
            self.build(courses, output)
            with zipfile.ZipFile(output) as archive:
                names = archive.namelist()
                self.assertIsNone(archive.testzip())
                self.assertIn("demo-practice/START_HERE.md", names)
                self.assertIn("demo-practice/workspace/game/main.py", names)
                self.assertIn("demo-practice/reference/game/main.py", names)
                self.assertTrue(all(not Path(name).is_absolute() for name in names))
                self.assertTrue(all(".." not in Path(name).parts for name in names))
                start = archive.read("demo-practice/START_HERE.md").decode("utf-8")
                self.assertIn("绿色基线不是完成实践", start)
                self.assertIn("cd workspace/game", start)

    def test_missing_quick_start_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            courses = root / "knowledge-sets"
            courses.mkdir()
            self.make_course(courses, {"quickStart": []})
            with self.assertRaisesRegex(ValueError, "quickStart"):
                self.build(courses, root / "demo.zip")

    def test_escaping_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            courses = root / "knowledge-sets"
            courses.mkdir()
            self.make_course(courses, {
                "include": [{"path": "code/game", "role": "editable-baseline", "target": "../escape"}]
            })
            with self.assertRaisesRegex(ValueError, "stay inside"):
                self.build(courses, root / "demo.zip")

    def test_windows_style_or_nonportable_target_is_rejected(self):
        for target in [r"..\\escape", r"C:\\escape", "bad:name", "trailing."]:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                courses = root / "knowledge-sets"
                courses.mkdir()
                self.make_course(courses, {
                    "include": [{"path": "code/game", "role": "editable-baseline", "target": target}]
                })
                with self.assertRaisesRegex(ValueError, "portable"):
                    self.build(courses, root / "demo.zip")

    def test_escaping_or_nested_bundle_name_is_rejected(self):
        for bundle_name in ["../escape", "nested/demo", r"C:\\escape", "bad:name"]:
            with self.subTest(bundle_name=bundle_name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                courses = root / "knowledge-sets"
                courses.mkdir()
                self.make_course(courses, {"bundleName": bundle_name})
                with self.assertRaises(ValueError):
                    self.build(courses, root / "demo.zip")

    def test_nested_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            courses = root / "knowledge-sets"
            courses.mkdir()
            course = self.make_course(courses)
            (course / "code/game/link.py").symlink_to(course / "code/game/main.py")
            with self.assertRaisesRegex(ValueError, "symlinks"):
                self.build(courses, root / "demo.zip")

    def test_duplicate_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            courses = root / "knowledge-sets"
            courses.mkdir()
            item = {"path": "code/game", "role": "editable-baseline", "target": "game"}
            self.make_course(courses, {"include": [item, item]})
            with self.assertRaisesRegex(ValueError, "duplicate bundle destination"):
                self.build(courses, root / "demo.zip")


if __name__ == "__main__":
    unittest.main()
