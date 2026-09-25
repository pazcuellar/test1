"""Splitting a chapter's text into lines and pages."""

from __future__ import annotations

from dataclasses import dataclass

from PIL import ImageFont

from .epub import Block


@dataclass(frozen=True, order=True)
class Position:
    """A place in a book that survives re-layout (e.g. a font size change)."""

    chapter: int = 0
    block: int = 0
    word: int = 0


@dataclass(frozen=True)
class Line:
    y: int
    text: str
    kind: str  # "heading" or "para"


@dataclass(frozen=True)
class Page:
    start: Position
    lines: list[Line]


@dataclass(frozen=True)
class TextStyle:
    body: ImageFont.FreeTypeFont
    heading: ImageFont.FreeTypeFont
    width: int
    height: int
    line_spacing: float = 1.25
    para_gap: int = 6
    heading_gap: int = 14


def paginate(blocks: list[Block], chapter: int, style: TextStyle) -> list[Page]:
    """Lay out one chapter. Returns no pages if the chapter has no text."""
    pages: list[Page] = []
    lines: list[Line] = []
    start = Position(chapter)
    y = 0
    for block_index, block in enumerate(blocks):
        font = style.heading if block.kind == "heading" else style.body
        ascent, descent = font.getmetrics()
        line_height = round((ascent + descent) * style.line_spacing)
        gap = (style.heading_gap if block.kind == "heading" else style.para_gap) if lines else 0
        for word_index, text in wrap(block.text.split(), font, style.width):
            if lines and y + gap + line_height > style.height:
                pages.append(Page(start, lines))
                lines, y, gap = [], 0, 0
            if not lines:
                start = Position(chapter, block_index, word_index)
            y += gap
            lines.append(Line(y, text, block.kind))
            y += line_height
            gap = 0
    if lines:
        pages.append(Page(start, lines))
    return pages


def wrap(words: list[str], font: ImageFont.FreeTypeFont, width: int):
    """Yield (index of first word, line text) for each line."""
    line: list[str] = []
    first = 0
    for index, word in enumerate(words):
        if line and font.getlength(" ".join(line + [word])) > width:
            yield first, " ".join(line)
            line = []
        if not line:
            first = index
            # A single word wider than the page (e.g. a URL) is cut up.
            while font.getlength(word) > width and len(word) > 1:
                cut = len(word) - 1
                while cut > 1 and font.getlength(word[:cut]) > width:
                    cut -= 1
                yield index, word[:cut]
                word = word[cut:]
        line.append(word)
    if line:
        yield first, " ".join(line)


def page_index(pages: list[Page], position: Position) -> int:
    """The page containing `position`."""
    index = 0
    for i, page in enumerate(pages):
        if page.start > position:
            break
        index = i
    return index
