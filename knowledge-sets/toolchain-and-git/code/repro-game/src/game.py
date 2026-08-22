#!/usr/bin/env python3
"""A deterministic, engine-free room generator used by the course lab."""
from __future__ import annotations

import argparse
import hashlib
import random

ROOM_COUNT = 5
ROOM_WIDTH = 9


def generate_room(seed: int, room_index: int) -> str:
    """Return a stable ASCII room for a seed and index.

    The derived seed keeps each room reproducible without sharing mutable global RNG state.
    """
    if room_index < 0:
        raise ValueError("room_index must be non-negative")
    rng = random.Random((seed * 1_000_003) ^ room_index)
    exit_column = rng.randrange(1, ROOM_WIDTH - 1)
    treasure_column = rng.randrange(1, ROOM_WIDTH - 1)
    if treasure_column == exit_column:
        treasure_column = (treasure_column % (ROOM_WIDTH - 2)) + 1
    row = ["."] * ROOM_WIDTH
    row[0] = "@"
    row[exit_column] = "E"
    row[treasure_column] = "T"
    return "".join(row)


def run(seed: int) -> str:
    rooms = [generate_room(seed, index) for index in range(ROOM_COUNT)]
    digest = hashlib.sha256("\n".join(rooms).encode("utf-8")).hexdigest()[:12]
    return f"seed={seed} checksum={digest}\n" + "\n".join(
        f"room {index}: {room}" for index, room in enumerate(rooms)
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    print(run(args.seed))


if __name__ == "__main__":
    main()
