#!/usr/bin/env python3
"""Run published reference-code regressions only in fresh temporary copies.

Python 3.9+, Make, C17 compiler. --sanitize additionally requires ASan/UBSan.
No existing .practice directory is read or modified.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> None:
    print("RUN", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, check=True, timeout=180,
                   env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sanitize", action="store_true")
    parser.add_argument("--bundles", action="store_true",
                        help="test freshly packaged and extracted downloads instead of source copies")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="game-knowledge-tests-") as directory:
        temporary = Path(directory)
        for slug, folder in [("toolchain-and-git", "repro-game"), ("c-programming", "runtime-kit")]:
            source = ROOT / "knowledge-sets" / slug / "code" / folder
            target = temporary / folder
            if args.bundles:
                archive_path = temporary / f"{slug}.zip"
                run([sys.executable, str(ROOT / "scripts/package_practice.py"),
                     "--course", slug, "--output", str(archive_path)], ROOT)
                with zipfile.ZipFile(archive_path) as archive:
                    if archive.testzip() is not None:
                        raise ValueError(f"corrupt archive: {slug}")
                    for name in archive.namelist():
                        path = Path(name)
                        if path.is_absolute() or ".." in path.parts:
                            raise ValueError(f"unsafe archive member: {name}")
                    archive.extractall(temporary / slug)
                target = temporary / slug / f"{slug}-practice" / "reference" / folder
            else:
                shutil.copytree(source, target, ignore=shutil.ignore_patterns(
                    "__pycache__", "*.pyc", "*.dSYM", "dist", "arena", "arena_asan",
                    "test_runtime", "test_runtime_asan", "test_cli", "test_cli_asan"))
            if slug == "toolchain-and-git":
                run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], target)
                run([sys.executable, "src/build.py", "--output", "dist", "--seed", "42"], target)
                run([sys.executable, "dist/game.py", "--seed", "42"], target)
                run([sys.executable, "src/build.py", "--output", "dist", "--clean"], target)
            else:
                run(["make", "test", f"PYTHON={sys.executable}"], target)
                if args.sanitize:
                    run(["make", "asan", f"PYTHON={sys.executable}"], target)
    print("REFERENCE CODE OK (not a certification of teaching completeness)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
