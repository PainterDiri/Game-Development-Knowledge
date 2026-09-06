"""Exercise destructive boundaries only in disposable temporary projects."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
import build


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "project"
        (self.root / "src").mkdir(parents=True)
        self.source = self.root / "src/game.py"
        self.source.write_text("print('room')\n", encoding="utf-8")
        for name, value in [("ROOT", self.root), ("SOURCE", self.source)]:
            patcher = patch.object(build, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(build, "git_value", return_value="unavailable")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_build_repeat_and_clean(self):
        output = self.root / "dist"
        build.build(output, 42, "1.0.0")
        first = {p.name: p.read_bytes() for p in output.iterdir()}
        build.build(output, 42, "1.0.0")
        self.assertEqual(first, {p.name: p.read_bytes() for p in output.iterdir()})
        manifest = json.loads(first["build-manifest.json"])
        self.assertEqual(manifest["deterministic"]["inputs"][0]["sha256"], build.sha256(self.source))
        build.clean(output)
        self.assertFalse(output.exists())
        self.assertTrue(self.source.exists())
        build.clean(output)

    def test_protected_and_external_paths_are_untouched(self):
        outside = self.root.parent / "outside"
        outside.mkdir()
        sentinel = outside / "important.txt"
        sentinel.write_text("keep", encoding="utf-8")
        for output in [self.root, self.root / "src", outside, self.root / "dist/../src"]:
            for action in [lambda p: build.build(p, 42, "1"), build.clean]:
                with self.subTest(output=output), self.assertRaises(ValueError):
                    action(output)
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertEqual(self.source.read_text(), "print('room')\n")

    def test_unknown_file_is_not_deleted_or_overwritten(self):
        output = self.root / "dist"
        build.build(output, 42, "1")
        sentinel = output / "notes.txt"
        sentinel.write_text("keep", encoding="utf-8")
        before = {name: (output / name).read_bytes() for name in build.OUTPUT_FILES}
        with self.assertRaises(ValueError):
            build.build(output, 43, "2")
        with self.assertRaises(ValueError):
            build.clean(output)
        self.assertEqual(sentinel.read_text(), "keep")
        self.assertEqual({name: (output / name).read_bytes() for name in build.OUTPUT_FILES}, before)

    def test_links_and_unrecognized_manifests_are_rejected(self):
        output = self.root / "dist"
        output.symlink_to(self.root / "src", target_is_directory=True)
        with self.assertRaises(ValueError):
            build.build(output, 42, "1")
        output.unlink()
        output.mkdir()
        (output / "game.py").symlink_to(self.source)
        with self.assertRaises(ValueError):
            build.clean(output)
        (output / "game.py").unlink()
        (output / "build-manifest.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            build.build(output, 42, "1")

    def test_nested_outputs_do_not_authorize_cleaning_parent(self):
        build.build(self.root / "dist/a", 42, "1")
        build.build(self.root / "dist/b", 43, "1")
        with self.assertRaises(ValueError):
            build.clean(self.root / "dist")
        build.clean(self.root / "dist/a")
        self.assertTrue((self.root / "dist/b/game.py").is_file())


if __name__ == "__main__":
    unittest.main()
