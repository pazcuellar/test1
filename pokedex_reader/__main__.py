"""Run the reader: python -m pokedex_reader [--books DIR]"""

from __future__ import annotations

import argparse
from pathlib import Path

from .app import run
from .progress import ProgressStore
from .screens import Context

WIDTH, HEIGHT = 300, 400  # the 4.2" panel held upright


def main() -> None:
    parser = argparse.ArgumentParser(prog="pokedex_reader", description=__doc__)
    parser.add_argument("--books", type=Path, default=Path.home() / "Books",
                        help="folder with .epub files (default: ~/Books)")
    parser.add_argument("--state", type=Path, default=Path.home() / ".pokedex-reader" / "progress.json",
                        help="where reading progress is saved")
    parser.add_argument("--landscape", action="store_true", help="use the panel sideways (400x300)")
    parser.add_argument("--scale", type=int, default=2, help="simulator window zoom (default: 2)")
    args = parser.parse_args()

    width, height = (HEIGHT, WIDTH) if args.landscape else (WIDTH, HEIGHT)
    from .simulator import Simulator  # only the laptop version needs pygame

    run(Simulator(width, height, args.scale),
        Context(width, height, args.books.expanduser(), ProgressStore(args.state)))


if __name__ == "__main__":
    main()
