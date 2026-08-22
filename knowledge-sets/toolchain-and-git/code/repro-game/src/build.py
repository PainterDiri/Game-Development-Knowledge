#!/usr/bin/env python3
"""Clean-build the deterministic course game and emit provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src" / "game.py"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build(output: Path, seed: int, version: str) -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    if output.exists():
        shutil.rmtree(output)
    game_dir = output
    game_dir.mkdir(parents=True)
    target = game_dir / "game.py"
    shutil.copy2(SOURCE, target)
    manifest = {
        "schema": 1,
        "game_version": version,
        "seed": seed,
        "commit": git_value("rev-parse", "HEAD"),
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "command": f"python3 src/build.py --output {output.name} --seed {seed} --version {version}",
        "inputs": [{"path": "src/game.py", "sha256": sha256(SOURCE)}],
        "deterministic": True,
    }
    (game_dir / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--version", default="0.1.0")
    args = parser.parse_args()
    build(args.output, args.seed, args.version)
    print(f"built {args.output}")


if __name__ == "__main__":
    main()
