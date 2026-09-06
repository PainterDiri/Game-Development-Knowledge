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


OUTPUT_FILES = {"game.py", "build-manifest.json"}


def validate_output(output: Path) -> Path:
    """Only own artifacts inside ROOT/dist; never recursively delete an argument."""
    if ".." in output.parts:
        raise ValueError("output must not contain '..'")
    root = ROOT.resolve()
    candidate = output if output.is_absolute() else Path.cwd() / output
    # Resolve the project prefix, but reject links in the managed subtree.
    if not candidate.is_relative_to(root / "dist"):
        raise ValueError("output must be dist or a directory inside this project's dist")
    relative = candidate.relative_to(root)
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("output path must not contain symbolic links")
    candidate = candidate.resolve()
    if candidate.exists():
        if not candidate.is_dir():
            raise ValueError("output must be a directory")
        for child in candidate.iterdir():
            if child.name not in OUTPUT_FILES or child.is_symlink() or not child.is_file():
                raise ValueError("output contains unowned files, directories, or symbolic links")
        manifest_path = candidate / "build-manifest.json"
        if any(candidate.iterdir()):
            if not manifest_path.is_file():
                raise ValueError("nonempty output has no build manifest; refusing to overwrite")
            try:
                old = json.loads(manifest_path.read_text(encoding="utf-8"))
                is_owned = old.get("schema") == 2 and old.get("provenance", {}).get("builder") == "src/build.py"
            except (ValueError, AttributeError):
                is_owned = False
            if not is_owned:
                raise ValueError("output manifest is not recognized")
    return candidate


def clean(output: Path) -> None:
    output = validate_output(output)
    if not output.exists():
        return
    for name in sorted(OUTPUT_FILES):
        (output / name).unlink(missing_ok=True)
    output.rmdir()


def build(output: Path, seed: int, version: str, target: str = "source-python") -> None:
    if not SOURCE.is_file():
        raise FileNotFoundError(SOURCE)
    output = validate_output(output)
    output.mkdir(parents=True, exist_ok=True)
    target_file = output / "game.py"
    shutil.copy2(SOURCE, target_file)
    commit = git_value("rev-parse", "HEAD")
    relative_output = output.relative_to(ROOT.resolve())
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
            "does not provide atomic publication or defend against concurrent malicious filesystem changes",
            "source_commit alone does not identify uncommitted input; inspect input hashes",
            "does not include external dependencies because the practice uses the standard library only",
        ],
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--clean", action="store_true", help="remove only recognized output files")
    parser.add_argument("--version", default="0.1.0")
    parser.add_argument("--target", default="source-python")
    args = parser.parse_args()
    if not args.clean and args.seed is None:
        parser.error("--seed is required unless --clean is used")
    try:
        if args.clean:
            clean(args.output)
        else:
            build(args.output, args.seed, args.version, args.target)
    except (ValueError, OSError) as error:
        parser.exit(2, f"build rejected: {error}\n")
    print(f"{'cleaned' if args.clean else 'built'} {args.output}")


if __name__ == "__main__":
    main()
