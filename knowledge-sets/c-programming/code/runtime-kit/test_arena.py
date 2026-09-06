"""Black-box CLI regression tests; Python 3.9+, standard library only."""
import re
import subprocess
import sys
import unittest
from pathlib import Path

ARENA = str(Path(sys.argv.pop(1) if len(sys.argv) > 1 else "./arena").resolve())


def run(data, *args):
    return subprocess.run([ARENA, *args], input=data, capture_output=True, timeout=10)


class ArenaTests(unittest.TestCase):
    def test_rejects_bad_lines_without_mutation_and_recovers(self):
        bad_lines = [b"wave 3x", b"wave -1", b"wave 2 extra", b"wave " + b"9" * 1000,
                     b"wave 2" + b" " * 130 + b"wave 1", b"wave 2\0hidden", b"quitx"]
        for bad in bad_lines:
            with self.subTest(line=bad[:30]):
                result = run(bad + b"\nstatus\nwave 1\nstatus\nquit\n")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.count(b"invalid command:"), 1)
                states = re.findall(rb"wave=\d+ player_hp=\d+ enemies=\d+ checksum=[0-9a-f]+", result.stdout)
                self.assertEqual(len(states), 3)
                self.assertEqual(states[0], states[1])
                self.assertIn(b"wave=1 player_hp=40 enemies=1", states[2])

    def test_seed_boundaries(self):
        for seed in ["-1", "+1", "4294967296", "bad", "9" * 1000]:
            self.assertEqual(run(b"", "--seed", seed).returncode, 2)
        for seed in ["0", "42", "4294967295"]:
            self.assertEqual(run(b"quit", "--seed", seed).returncode, 0)

    def test_same_command_sequence_is_reproducible(self):
        data = b"wave 3\nhit 0 999\nenemy\nstatus\nquit\n"
        first, second = run(data, "--seed", "42"), run(data, "--seed", "42")
        self.assertEqual(first.returncode, 0)
        self.assertEqual(second.returncode, 0)
        self.assertEqual(first.stdout, second.stdout)

    def test_final_line_without_newline_and_long_eof(self):
        self.assertIn(b"result=0", run(b"wave 1").stdout)
        self.assertEqual(run(b"wave 1" + b" " * 200).stdout.count(b"invalid command:"), 1)


if __name__ == "__main__":
    unittest.main()
