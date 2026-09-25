"""Drive the whole reader with scripted button presses."""

from pokedex_reader.device import Button
from pokedex_reader.layout import Position
from pokedex_reader.progress import ProgressStore
from pokedex_reader.screens import Context, LibraryScreen, ReaderScreen, start_screen


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
