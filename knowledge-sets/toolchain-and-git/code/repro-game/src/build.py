#!/usr/bin/env python3
"""Clean-build the deterministic course game and emit a traceable manifest.

Python: 3.11+ (standard library only)
Run from this directory, for example:
    python3 src/build.py --output dist --seed 42 --version 1.0.0

The manifest deliberately separates deterministic comparison fields from
provenance fields. It is evidence about this small practice, not a complete
software-supply-chain attestation.
"""
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
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build(output: Path, seed: int, version: str, target: str = "source-python") -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    if output.exists():
        shutil.rmtree(output)

    output.mkdir(parents=True)
    target_file = output / "game.py"
    shutil.copy2(SOURCE, target_file)
    commit = git_value("rev-parse", "HEAD")
    relative_output = output.relative_to(ROOT) if output.is_relative_to(ROOT) else Path(output.name)
    manifest = {
        "schema": 2,
        "deterministic": {
            "game_version": version,
            "source_commit": commit,
            "target": target,
            "seed": seed,
            "inputs": [{"path": "src/game.py", "sha256": sha256(SOURCE)}],
            "comparison": "byte-identical for this engine-free practice output",
        },
        "provenance": {
            "builder": "src/build.py",
            "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "command": f"python3 src/build.py --output {relative_output.as_posix()} --seed {seed} --version {version}",
        },
        "limitations": [
            "does not attest the Python interpreter or operating system",
            "does not include external dependencies because the practice uses the standard library only",
        ],
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--target", default="source-python")
    args = parser.parse_args()
    build(args.output, args.seed, args.version, args.target)
    print(f"built {args.output}")


if __name__ == "__main__":
    main()
