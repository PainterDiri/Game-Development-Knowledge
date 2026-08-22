import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from game import ROOM_COUNT, generate_room, run  # noqa: E402


class GameTests(unittest.TestCase):
    def test_same_seed_is_reproducible(self):
        self.assertEqual(run(42), run(42))

    def test_different_seed_changes_the_run(self):
        self.assertNotEqual(run(42), run(43))

    def test_each_room_has_start_exit_and_treasure(self):
        self.assertEqual(len([generate_room(7, i) for i in range(ROOM_COUNT)]), ROOM_COUNT)
        for index in range(ROOM_COUNT):
            room = generate_room(7, index)
            self.assertEqual(room.count("@"), 1)
            self.assertEqual(room.count("E"), 1)
            self.assertEqual(room.count("T"), 1)

    def test_invalid_room_is_rejected(self):
        with self.assertRaises(ValueError):
            generate_room(1, -1)
