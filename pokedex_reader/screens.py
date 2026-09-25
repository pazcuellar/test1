"""The library, reading, menu and contents screens.

Each screen draws itself as an image and reacts to a button or a tap by
returning the screen to show next (itself, to stay). Screens ask for chimes
and cover-light animations with `ctx.play(effect)`.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from PIL import Image, ImageDraw

from . import fonts
from .device import BLACK, DARK, LIGHT, WHITE, Button
from .effects import Effect
from .epub import Book, EpubError
from .layout import Page, Position, TextStyle, page_index, paginate
from .progress import ProgressStore

MARGIN = 16
HEADER = 44
FOOTER = 22
FONT_SIZES = (14, 17, 20, 24, 28)
DEFAULT_FONT_SIZE = 1  # index into FONT_SIZES


@dataclass
class Context:
    width: int
    height: int
    books_dir: Path
    progress: ProgressStore
    koreader: list[str] | None = None  # command that starts KOReader
    _books: list[tuple[str, Book]] | None = field(default=None, repr=False)

    def __post_init__(self):
        self.effects: list[Effect] = []
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

    def play(self, effect: Effect) -> None:
        self.effects.append(effect)

    def take_effects(self) -> list[Effect]:
        effects, self.effects = self.effects, []
        return effects

    def blank(self) -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("L", (self.width, self.height), WHITE)
        return image, ImageDraw.Draw(image)


def start_screen(ctx: Context):
    """Reopen the last book at its page, as if waking up; else the library."""
    for name, book in ctx.books():
        if name == ctx.progress.last_book:
            return ReaderScreen(ctx, name, book)
    return LibraryScreen(ctx)


def draw_header(ctx: Context, draw: ImageDraw.ImageDraw, title: str) -> None:
    draw.rectangle([0, 0, ctx.width, HEADER - 1], fill=BLACK)
    # The big blue lens and the three small lights of the Kanto Pokédex.
    cx, cy, r = 24, HEADER // 2, 14
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=WHITE)
    draw.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], fill=LIGHT)
    draw.ellipse([cx - 7, cy - 8, cx - 2, cy - 3], fill=WHITE)
    for i, shade in enumerate((WHITE, LIGHT, DARK)):
        x = 48 + i * 11
        draw.ellipse([x, 8, x + 6, 14], fill=shade, outline=WHITE)
    draw.text((48, HEADER - 8), _fit(title, ctx.title_font, ctx.width - 48 - MARGIN),
              font=ctx.title_font, fill=WHITE, anchor="ls")


def draw_pokeball(draw: ImageDraw.ImageDraw, center: tuple[int, int], r: int,
                  ink: int, paper: int, caught: bool) -> None:
    """Seen books get an outline; caught (finished) ones a filled top half."""
    x, y = center
    box = [x - r, y - r, x + r, y + r]
    draw.ellipse(box, fill=paper, outline=ink, width=2)
    if caught:
        draw.pieslice(box, 180, 360, fill=ink)
    draw.line([(x - r, y), (x + r, y)], fill=ink, width=2)
    draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=paper, outline=ink, width=2)


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
        draw_header(ctx, draw, "POKÉDEX")
        books = ctx.books()
        if not books:
            draw.multiline_text(
                (MARGIN, HEADER + MARGIN),
                f"No books yet.\n\nCopy .epub files into:\n{ctx.books_dir}",
                font=ctx.ui_font, fill=BLACK, spacing=6)
        visible = (ctx.height - HEADER - FOOTER) // self.ROW
        self.top = min(max(self.top, self.selected - visible + 1), self.selected)
        text_width = ctx.width - MARGIN * 2 - 66 - 24
        for row, (name, book) in enumerate(books[self.top:self.top + visible]):
            number = self.top + row
            y = HEADER + row * self.ROW
            ink, paper = BLACK, WHITE
            if number == self.selected:
                draw.rectangle([0, y, ctx.width, y + self.ROW - 1], fill=BLACK)
                ink, paper = WHITE, BLACK
            draw.text((MARGIN, y + 8), f"No.{number + 1:03d}", font=ctx.ui_bold, fill=ink)
            draw.text((MARGIN + 66, y + 8), _fit(book.title, ctx.ui_bold, text_width),
                      font=ctx.ui_bold, fill=ink)
            draw.text((MARGIN + 66, y + 27), _fit(book.author, ctx.ui_font, text_width),
                      font=ctx.ui_font, fill=LIGHT if number == self.selected else DARK)
            caught = ctx.progress.is_finished(name)
            if caught or ctx.progress.position(name):
                draw_pokeball(draw, (ctx.width - MARGIN - 8, y + self.ROW // 2), 8, ink, paper, caught)
        seen = sum(1 for name, _ in books
                   if ctx.progress.position(name) or ctx.progress.is_finished(name))
        caught = sum(1 for name, _ in books if ctx.progress.is_finished(name))
        draw_footer(ctx, draw, "A open   B menu" if ctx.koreader else "A open   ▲▼ choose",
                    f"seen {seen} · caught {caught}" if books else "")
        return image

    def handle(self, button: Button):
        books = self.ctx.books()
        if button == Button.DOWN and self.selected < len(books) - 1:
            self.selected += 1
        elif button == Button.UP and self.selected > 0:
            self.selected -= 1
        elif button == Button.A and books:
            name, book = books[self.selected]
            self.ctx.play(Effect.OPEN_BOOK)
            return ReaderScreen(self.ctx, name, book)
        elif button == Button.B and (items := koreader_item(self.ctx, self)):
            self.ctx.play(Effect.SELECT)
            return MenuScreen(self.ctx, self, items)
        return self

    def tap(self, x: int, y: int):
        row = self.top + (y - HEADER) // self.ROW
        if y >= HEADER and row < len(self.ctx.books()):
            self.selected = row
            return self.handle(Button.A)
        return self


class ReaderScreen:
    def __init__(self, ctx: Context, name: str, book: Book):
        self.ctx = ctx
        self.name = name
        self.book = book
        saved = ctx.progress.setting("font_size", DEFAULT_FONT_SIZE)
        self.font_size = min(max(int(saved), 0), len(FONT_SIZES) - 1)
        self._set_style()

        position = ctx.progress.position(name) or Position()
        chapter = min(position.chapter, len(book.chapter_files) - 1)
        if chapter >= 0 and self.pages(chapter):
            self.chapter = chapter
        else:  # e.g. a cover page that is only an image
            forward = self._next_chapter_with_text(chapter, +1)
            self.chapter = forward if forward is not None else self._next_chapter_with_text(chapter, -1)
        self.page = page_index(self.pages(self.chapter), position) if self.chapter is not None else 0
        # Where you actually are. Re-layouts (font size changes) find their
        # page from this, so repeated changes don't drift backwards.
        self.anchor = position
        if self.chapter is not None and self.chapter != position.chapter:
            self._save()

    def _set_style(self) -> None:
        size = FONT_SIZES[self.font_size]
        self.style = TextStyle(
            body=fonts.load(fonts.SERIF, size),
            heading=fonts.load(fonts.SERIF_BOLD, round(size * 1.25)),
            width=self.ctx.width - MARGIN * 2,
            height=self.ctx.height - MARGIN - FOOTER - 6,
        )
        self._pages: dict[int, list[Page]] = {}

    def change_font_size(self, step: int) -> None:
        """Make text bigger (+1) or smaller (-1), staying on the same text."""
        size = min(max(self.font_size + step, 0), len(FONT_SIZES) - 1)
        if size == self.font_size:
            return
        self.font_size = size
        self.ctx.progress.set_setting("font_size", size)
        if self.chapter is None:
            return self._set_style()
        self._set_style()
        self.page = page_index(self.pages(self.chapter), self.anchor)

    def go_to_chapter(self, chapter: int) -> None:
        if not self.pages(chapter):
            chapter = self._next_chapter_with_text(chapter, +1)
        if chapter is not None:
            self.chapter, self.page = chapter, 0
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
        """Called after moving: the new page's start becomes your place."""
        if self.chapter is not None:
            self.anchor = self.pages(self.chapter)[self.page].start
            self.ctx.progress.save(self.name, self.anchor)

    def render(self) -> Image.Image:
        ctx = self.ctx
        image, draw = ctx.blank()
        if self.chapter is None:
            draw.text((MARGIN, MARGIN), "This book has no text.", font=ctx.ui_font, fill=BLACK)
            draw_footer(ctx, draw, "A menu   B library")
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
            self.ctx.play(Effect.BACK)
            self.ctx.progress.forget_last_book()
            names = [name for name, _ in self.ctx.books()]
            return LibraryScreen(self.ctx, selected=names.index(self.name))
        if button == Button.A:
            self.ctx.play(Effect.SELECT)
            return reader_menu(self)
        if self.chapter is None:
            return self
        if button == Button.RIGHT:
            if self.page < len(self.pages(self.chapter)) - 1:
                self.page += 1
            elif (chapter := self._next_chapter_with_text(self.chapter, +1)) is not None:
                self.chapter, self.page = chapter, 0
            else:  # pressed "next" on the very last page
                if not self.ctx.progress.is_finished(self.name):
                    self.ctx.progress.mark_finished(self.name)
                    self.ctx.play(Effect.CAUGHT)
                return self
            self.ctx.play(Effect.PAGE)
        elif button == Button.LEFT:
            if self.page > 0:
                self.page -= 1
            elif (chapter := self._next_chapter_with_text(self.chapter, -1)) is not None:
                self.chapter, self.page = chapter, len(self.pages(chapter)) - 1
            else:
                return self
            self.ctx.play(Effect.PAGE)
        else:
            return self
        self._save()
        return self

    def tap(self, x: int, y: int):
        """Left third: back a page. Right third: forward. Middle: menu."""
        if x < self.ctx.width // 3:
            return self.handle(Button.LEFT)
        if x >= self.ctx.width * 2 // 3:
            return self.handle(Button.RIGHT)
        return self.handle(Button.A)


@dataclass
class MenuItem:
    label: str
    select: Callable[[], object]  # returns the next screen
    adjust: Callable[[int], None] | None = None  # ◀ ▶ changes a value
    value: Callable[[], str] | None = None  # shown on the right
    effect: Effect | None = Effect.SELECT


@dataclass(frozen=True)
class Launch:
    """Returned instead of a screen: run another program (e.g. KOReader)
    with the screen and buttons handed over, then show `return_to`."""

    command: list[str]
    return_to: object


class MenuScreen:
    """A panel of items drawn over another screen. B closes it."""

    ROW = 30

    def __init__(self, ctx: Context, base, items: list[MenuItem]):
        self.ctx = ctx
        self.base = base
        self.items = items
        self.selected = 0

    def render(self) -> Image.Image:
        ctx = self.ctx
        image = self.base.render()
        draw = ImageDraw.Draw(image)
        top = self._top()
        draw.rectangle([0, top, ctx.width, ctx.height], fill=WHITE)
        draw.rectangle([0, top, ctx.width, top + 3], fill=BLACK)
        for i, item in enumerate(self.items):
            y = top + 8 + i * self.ROW
            ink = BLACK
            if i == self.selected:
                draw.rectangle([MARGIN // 2, y, ctx.width - MARGIN // 2, y + self.ROW - 4], fill=BLACK)
                ink = WHITE
            middle = y + (self.ROW - 4) // 2
            draw.text((MARGIN, middle), item.label, font=ctx.ui_bold, fill=ink, anchor="lm")
            if item.value:
                draw.text((ctx.width - MARGIN, middle), item.value(), font=ctx.ui_font, fill=ink, anchor="rm")
        hint = "\u25c0 \u25b6 change" if self.items[self.selected].adjust else ""
        draw_footer(ctx, draw, "A choose   B close", hint)
        return image

    def _top(self) -> int:
        return self.ctx.height - FOOTER - len(self.items) * self.ROW - 12

    def handle(self, button: Button):
        item = self.items[self.selected]
        if button == Button.DOWN:
            self.selected = min(self.selected + 1, len(self.items) - 1)
        elif button == Button.UP:
            self.selected = max(self.selected - 1, 0)
        elif button in (Button.LEFT, Button.RIGHT) and item.adjust:
            item.adjust(+1 if button == Button.RIGHT else -1)
            self.ctx.play(Effect.PAGE)
        elif button == Button.B:
            self.ctx.play(Effect.BACK)
            return self.base
        elif button == Button.A:
            if item.effect:
                self.ctx.play(item.effect)
            return item.select()
        return self

    def tap(self, x: int, y: int):
        """Tap an item to choose it; tap the left or right side of an
        adjustable item to change it; tap above the panel to close."""
        top = self._top()
        if y < top:
            return self.handle(Button.B)
        row = (y - top - 8) // self.ROW
        if not 0 <= row < len(self.items):
            return self
        self.selected = row
        if self.items[row].adjust:
            return self.handle(Button.LEFT if x < self.ctx.width * 3 // 4 else Button.RIGHT)
        return self.handle(Button.A)


def koreader_item(ctx: Context, return_to) -> list[MenuItem]:
    if not ctx.koreader:
        return []
    return [MenuItem("KOReader", lambda: Launch(ctx.koreader, return_to))]


def reader_menu(reader: ReaderScreen) -> MenuScreen:
    ctx = reader.ctx

    def sizes() -> str:
        dots = "  ".join("\u25cf" if n == reader.font_size else "\u25cb" for n in range(len(FONT_SIZES)))
        return f"\u25c0 {dots} \u25b6"

    return MenuScreen(ctx, reader, [
        MenuItem("Text size", lambda: reader, adjust=reader.change_font_size, value=sizes),
        MenuItem("Contents", lambda: ContentsScreen(reader)),
        *koreader_item(ctx, reader),
        MenuItem("Library", lambda: reader.handle(Button.B), effect=None),
    ])


class ContentsScreen:
    """The book's chapters. A jumps to one, B goes back to the page."""

    ROW = 32

    def __init__(self, reader: ReaderScreen):
        self.reader = reader
        self.entries = reader.book.toc()
        current = reader.chapter or 0
        # The last entry at or before the current chapter.
        self.selected = max((i for i, e in enumerate(self.entries) if e.chapter <= current), default=0)
        self.top = 0

    def render(self) -> Image.Image:
        ctx = self.reader.ctx
        image, draw = ctx.blank()
        draw_header(ctx, draw, "CONTENTS")
        if not self.entries:
            draw.text((MARGIN, HEADER + MARGIN), "This book has no chapters.", font=ctx.ui_font, fill=BLACK)
        visible = (ctx.height - HEADER - FOOTER) // self.ROW
        self.top = min(max(self.top, self.selected - visible + 1), self.selected)
        for row, entry in enumerate(self.entries[self.top:self.top + visible]):
            y = HEADER + row * self.ROW
            ink = BLACK
            if self.top + row == self.selected:
                draw.rectangle([0, y, ctx.width, y + self.ROW - 1], fill=BLACK)
                ink = WHITE
            draw.text((MARGIN, y + self.ROW // 2), _fit(entry.title, ctx.ui_bold, ctx.width - MARGIN * 2),
                      font=ctx.ui_bold, fill=ink, anchor="lm")
        draw_footer(ctx, draw, "A go   B back", f"{self.selected + 1}/{len(self.entries)}" if self.entries else "")
        return image

    def handle(self, button: Button):
        if button == Button.DOWN:
            self.selected = min(self.selected + 1, max(len(self.entries) - 1, 0))
        elif button == Button.UP:
            self.selected = max(self.selected - 1, 0)
        elif button == Button.B:
            self.reader.ctx.play(Effect.BACK)
            return self.reader
        elif button == Button.A and self.entries:
            self.reader.ctx.play(Effect.SELECT)
            self.reader.go_to_chapter(self.entries[self.selected].chapter)
            return self.reader
        return self

    def tap(self, x: int, y: int):
        row = self.top + (y - HEADER) // self.ROW
        if y >= HEADER and row < len(self.entries):
            self.selected = row
            return self.handle(Button.A)
        return self


def _fit(text: str, font, width: int) -> str:
    """Shorten `text` with an ellipsis until it fits in `width` pixels."""
    if font.getlength(text) <= width:
        return text
    while text and font.getlength(text + "…") > width:
        text = text[:-1]
    return text.rstrip() + "…"
