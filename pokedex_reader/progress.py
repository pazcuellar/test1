"""Remembering the current page of each book, and the last book open."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .layout import Position


class ProgressStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            data = json.loads(self.path.read_text())
        except (OSError, ValueError):
            data = {}
        self.last_book: str | None = data.get("last_book")
        self._positions: dict[str, list[int]] = data.get("books", {})

    def position(self, book: str) -> Position | None:
        saved = self._positions.get(book)
        return Position(*saved) if saved else None

    def save(self, book: str, position: Position) -> None:
        self.last_book = book
        self._positions[book] = [position.chapter, position.block, position.word]
        self._write()

    def forget_last_book(self) -> None:
        self.last_book = None
        self._write()

    def _write(self) -> None:
        # Write to a temporary file and swap it in, so losing power
        # mid-write can't leave a half-written file behind.
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"last_book": self.last_book, "books": self._positions}))
        os.replace(tmp, self.path)
