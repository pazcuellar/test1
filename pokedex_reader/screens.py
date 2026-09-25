"""The library and reading screens.

Each screen draws itself as an image and reacts to a button by returning
the screen to show next (itself, to stay).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw

from . import fonts
from .device import BLACK, DARK, LIGHT, WHITE, Button
from .epub import Book, EpubError
from .layout import Page, Position, TextStyle, page_index, paginate
from .progress import ProgressStore

MARGIN = 16
HEADER = 44
FOOTER = 22


@dataclass
class Context:
    width: int
    height: int
    books_dir: Path
    progress: ProgressStore
    _books: list[tuple[str, Book]] | None = field(default=None, repr=False)

    def __post_init__(self):
        self.ui_font = fonts.load(fonts.SANS, 13)
        self.ui_bold = fonts.load(fonts.SANS_BOLD, 15)
        self.title_font = fonts.load(fonts.SANS_BOLD, 20)

    def books(self) -> list[tuple[str, Book]]:
        """(file name, book) for every readable EPUB in the books folder."""
        if self._books is None:
            self._books = []
            for path in sorted(self.books_dir.glob("*.epub"), key=lambda p: p.name.lower()):
                try:
                    self._books.append((path.name, Book(path)))
                except EpubError as e:
                    print(f"Skipping unreadable book: {e}", file=sys.stderr)
        return self._books

    def blank(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("L", (self.width, self.height), WHITE)
        return image, ImageDraw.Draw(image)


def start_screen(ctx: Context):
    """Reopen the last book at its page, as if waking up; else the library."""
    for name, book in ctx.books():
        if name == ctx.progress.last_book:
            return ReaderScreen(ctx, name, book)
    return LibraryScreen(ctx)


def draw_footer(ctx: Context, draw: ImageDraw.ImageDraw, left: str, right: str = "") -> None:
    top = ctx.height - FOOTER
    draw.line([(0, top), (ctx.width, top)], fill=DARK)
    middle = top + FOOTER // 2
    draw.text((MARGIN, middle), left, font=ctx.ui_font, fill=DARK, anchor="lm")
    draw.text((ctx.width - MARGIN, middle), right, font=ctx.ui_font, fill=DARK, anchor="rm")


class LibraryScreen:
    ROW = 46

    def __init__(self, ctx: Context, selected: int = 0):
        self.ctx = ctx
        self.selected = selected
        self.top = 0  # first visible row

    def render(self) -> Image.Image:
        ctx = self.ctx
        image, draw = ctx.blank()
        self._draw_header(draw)
        books = ctx.books()
        if not books:
            draw.multiline_text(
                (MARGIN, HEADER + MARGIN),
                f"No books yet.\n\nCopy .epub files into:\n{ctx.books_dir}",
                font=ctx.ui_font, fill=BLACK, spacing=6)
        visible = (ctx.height - HEADER - FOOTER) // self.ROW
        self.top = min(max(self.top, self.selected - visible + 1), self.selected)
        for row, (_, book) in enumerate(books[self.top:self.top + visible]):
            number = self.top + row
            y = HEADER + row * self.ROW
            ink = BLACK
            if number == self.selected:
                draw.rectangle([0, y, ctx.width, y + self.ROW - 1], fill=BLACK)
                ink = WHITE
            draw.text((MARGIN, y + 8), f"No.{number + 1:03d}", font=ctx.ui_bold, fill=ink)
            draw.text((MARGIN + 66, y + 8), _fit(book.title, ctx.ui_bold, ctx.width - MARGIN * 2 - 66),
                      font=ctx.ui_bold, fill=ink)
            draw.text((MARGIN + 66, y + 27), _fit(book.author, ctx.ui_font, ctx.width - MARGIN * 2 - 66),
                      font=ctx.ui_font, fill=LIGHT if number == self.selected else DARK)
        draw_footer(ctx, draw, "A open   ▲▼ choose", f"{len(books)} books" if books else "")
        return image

    def _draw_header(self, draw: ImageDraw.ImageDraw) -> None:
        ctx = self.ctx
        draw.rectangle([0, 0, ctx.width, HEADER - 1], fill=BLACK)
        # The big blue lens and the three small lights of the Kanto Pokédex.
        cx, cy, r = 24, HEADER // 2, 14
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
        draw.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=LIGHT)
        draw.ellipse([cx - 7, cy - 8, cx - 2, cy - 3], fill=WHITE)
        for i, shade in enumerate((WHITE, LIGHT, DARK)):
            x = 48 + i * 11
            draw.ellipse([x, 8, x + 6, 14], fill=shade, outline=WHITE)
        draw.text((48, HEADER - 8), "POKÉDEX", font=ctx.title_font, fill=WHITE, anchor="ls")

    def handle(self, button: Button):
        books = self.ctx.books()
        if button == Button.DOWN and self.selected < len(books) - 1:
            self.selected += 1
        elif button == Button.UP and self.selected > 0:
            self.selected -= 1
        elif button == Button.A and books:
            name, book = books[self.selected]
            return ReaderScreen(self.ctx, name, book)
        return self


class ReaderScreen:
    def __init__(self, ctx: Context, name: str, book: Book):
        self.ctx = ctx
        self.name = name
        self.book = book
        self.style = TextStyle(
            body=fonts.load(fonts.SERIF, 17),
            heading=fonts.load(fonts.SERIF_BOLD, 21),
            width=ctx.width - MARGIN * 2,
            height=ctx.height - MARGIN - FOOTER - 6,
        )
        self._pages: dict[int, list[Page]] = {}

        position = ctx.progress.position(name) or Position()
        chapter = min(position.chapter, len(book.chapter_files) - 1)
        if chapter >= 0 and self.pages(chapter):
            self.chapter = chapter
        else:  # e.g. a cover page that is only an image
            forward = self._next_chapter_with_text(chapter, +1)
            self.chapter = forward if forward is not None else self._next_chapter_with_text(chapter, -1)
        self.page = page_index(self.pages(self.chapter), position) if self.chapter is not None else 0
        self._save()

    def pages(self, chapter: int) -> list[Page]:
        if chapter not in self._pages:
            self._pages[chapter] = paginate(self.book.chapter(chapter), chapter, self.style)
        return self._pages[chapter]

    def _next_chapter_with_text(self, chapter: int, step: int) -> int | None:
        chapter += step
        while 0 <= chapter < len(self.book.chapter_files):
            if self.pages(chapter):
                return chapter
            chapter += step
        return None

    def _save(self) -> None:
        if self.chapter is not None:
            self.ctx.progress.save(self.name, self.pages(self.chapter)[self.page].start)

    def render(self) -> Image.Image:
        ctx = self.ctx
        image, draw = ctx.blank()
        if self.chapter is None:
            draw.text((MARGIN, MARGIN), "This book has no text.", font=ctx.ui_font, fill=BLACK)
            draw_footer(ctx, draw, "B library")
            return image
        pages = self.pages(self.chapter)
        for line in pages[self.page].lines:
            font = self.style.heading if line.kind == "heading" else self.style.body
            draw.text((MARGIN, MARGIN + line.y), line.text, font=font, fill=BLACK)
        chapters = len(self.book.chapter_files)
        draw_footer(ctx, draw, _fit(self.book.title, ctx.ui_font, ctx.width // 2),
                    f"ch {self.chapter + 1}/{chapters} · {self.page + 1}/{len(pages)}")
        return image

    def handle(self, button: Button):
        if button == Button.B:
            self.ctx.progress.forget_last_book()
            names = [name for name, _ in self.ctx.books()]
            return LibraryScreen(self.ctx, selected=names.index(self.name))
        if self.chapter is None:
            return self
        if button == Button.RIGHT:
            if self.page < len(self.pages(self.chapter)) - 1:
                self.page += 1
            elif (chapter := self._next_chapter_with_text(self.chapter, +1)) is not None:
                self.chapter, self.page = chapter, 0
        elif button == Button.LEFT:
            if self.page > 0:
                self.page -= 1
            elif (chapter := self._next_chapter_with_text(self.chapter, -1)) is not None:
                self.chapter, self.page = chapter, len(self.pages(chapter)) - 1
        self._save()
        return self


def _fit(text: str, font, width: int) -> str:
    """Shorten `text` with an ellipsis until it fits in `width` pixels."""
    if font.getlength(text) <= width:
        return text
    while text and font.getlength(text + "…") > width:
        text = text[:-1]
    return text.rstrip() + "…"
