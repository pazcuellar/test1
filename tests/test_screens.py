"""Drive the whole reader with scripted button presses."""

from pokedex_reader.device import Button
from pokedex_reader.layout import Position
from pokedex_reader.progress import ProgressStore
from pokedex_reader.screens import (
    DEFAULT_FONT_SIZE, FONT_SIZES, ContentsScreen, Context, LibraryScreen, MenuScreen, ReaderScreen,
    start_screen)


def make_ctx(books_dir, state_path):
    return Context(300, 400, books_dir, ProgressStore(state_path))


def press(screen, *buttons):
    for button in buttons:
        screen = screen.handle(button)
        assert screen.render().size == (300, 400)
    return screen


def test_library_lists_readable_books_sorted(books_dir, tmp_path, capsys):
    ctx = make_ctx(books_dir, tmp_path / "p.json")
    assert [book.title for _, book in ctx.books()] == ["Alpha Book", "Beta Book"]
    assert "broken.epub" in capsys.readouterr().err


def test_open_turn_pages_and_resume(books_dir, tmp_path):
    state = tmp_path / "p.json"
    screen = start_screen(make_ctx(books_dir, state))
    assert isinstance(screen, LibraryScreen)

    screen = press(screen, Button.DOWN, Button.A)  # open "Beta Book"
    assert isinstance(screen, ReaderScreen)
    assert screen.chapter == 1, "the image-only cover chapter is skipped"
    first_chapter_pages = len(screen.pages(1))

    screen = press(screen, *[Button.RIGHT] * (first_chapter_pages + 1))
    assert (screen.chapter, screen.page) == (2, 1)
    saved = ProgressStore(state).position("b.epub")
    assert saved == screen.pages(2)[1].start

    # Restarting (like opening the lid after a shutdown) goes straight back.
    screen = start_screen(make_ctx(books_dir, state))
    assert isinstance(screen, ReaderScreen)
    assert (screen.name, screen.chapter, screen.page) == ("b.epub", 2, 1)

    # Paging back across the chapter boundary lands on the last page.
    screen = press(screen, Button.LEFT, Button.LEFT)
    assert (screen.chapter, screen.page) == (1, first_chapter_pages - 1)
    # ...but never into the empty cover chapter.
    screen = press(screen, *[Button.LEFT] * (first_chapter_pages + 5))
    assert (screen.chapter, screen.page) == (1, 0)


def test_back_returns_to_library_on_the_same_book(books_dir, tmp_path):
    state = tmp_path / "p.json"
    screen = press(start_screen(make_ctx(books_dir, state)), Button.DOWN, Button.A, Button.RIGHT)
    screen = press(screen, Button.B)
    assert isinstance(screen, LibraryScreen)
    assert screen.selected == 1
    # Leaving the book means the next start shows the library.
    assert isinstance(start_screen(make_ctx(books_dir, state)), LibraryScreen)
    # The page is still remembered for when the book is reopened.
    assert ProgressStore(state).position("b.epub") > Position(1, 0, 0)


def test_last_page_of_book_stays_put(books_dir, tmp_path):
    screen = press(start_screen(make_ctx(books_dir, tmp_path / "p.json")), Button.A)
    pages = len(screen.pages(0))
    screen = press(screen, *[Button.RIGHT] * (pages + 3))
    assert (screen.chapter, screen.page) == (0, pages - 1)


def test_empty_library_renders(tmp_path):
    screen = start_screen(make_ctx(tmp_path, tmp_path / "p.json"))
    assert press(screen, Button.A, Button.DOWN).render().size == (300, 400)


def test_font_size_keeps_your_place_and_is_remembered(books_dir, tmp_path):
    state = tmp_path / "p.json"
    screen = press(start_screen(make_ctx(books_dir, state)), Button.A, Button.RIGHT, Button.RIGHT)
    reader = screen
    words_at_top = reader.pages(reader.chapter)[reader.page].start
    small_pages = len(reader.pages(reader.chapter))

    menu = press(reader, Button.A)
    assert isinstance(menu, MenuScreen)
    press(menu, Button.RIGHT, Button.RIGHT)  # two sizes bigger
    assert reader.font_size == DEFAULT_FONT_SIZE + 2
    assert len(reader.pages(reader.chapter)) > small_pages

    def shows_words_at_top():
        """The page shown still contains the text that was at the top before."""
        pages = reader.pages(reader.chapter)
        return pages[reader.page].start <= words_at_top and (
            reader.page == len(pages) - 1 or pages[reader.page + 1].start > words_at_top)

    assert shows_words_at_top()
    # Going up to the biggest size and back down doesn't lose your place.
    press(menu, *[Button.RIGHT] * 10)
    assert reader.font_size == len(FONT_SIZES) - 1
    assert shows_words_at_top()
    press(menu, *[Button.LEFT] * 10)
    assert reader.font_size == 0
    assert shows_words_at_top()
    press(menu, *[Button.RIGHT] * 10)
    assert press(menu, Button.B) is reader

    assert ReaderScreen(make_ctx(books_dir, state), "a.epub", reader.book).font_size == len(FONT_SIZES) - 1


def test_contents_jumps_to_a_chapter(books_dir, tmp_path):
    screen = press(start_screen(make_ctx(books_dir, tmp_path / "p.json")), Button.DOWN, Button.A)
    assert screen.chapter == 1
    contents = press(screen, Button.A, Button.DOWN, Button.A)  # menu -> Contents
    assert isinstance(contents, ContentsScreen)
    assert [e.title for e in contents.entries] == ["One", "Two"]
    assert contents.selected == 0, "starts on the current chapter"
    reader = press(contents, Button.DOWN, Button.A)
    assert reader is screen
    assert (reader.chapter, reader.page) == (2, 0)
    assert isinstance(press(reader, Button.A, Button.DOWN, Button.DOWN, Button.A), LibraryScreen)
