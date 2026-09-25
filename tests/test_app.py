"""Run the main loop against a scripted fake device."""

import sys

from pokedex_reader.app import run
from pokedex_reader.device import Button, Device, DeviceClosed, Tap
from pokedex_reader.effects import Effect
from pokedex_reader.progress import ProgressStore
from pokedex_reader.screens import Context, LibraryScreen, MenuScreen, ReaderScreen


class FakeDevice(Device):
    width, height = 300, 400

    def __init__(self, inputs):
        self.inputs = list(inputs)
        self.frames = []
        self.effects = []
        self.closed = False

    def show(self, image):
        assert image.size == (300, 400)
        self.frames.append(image)

    def wait_input(self):
        if not self.inputs:
            raise DeviceClosed
        return self.inputs.pop(0)

    def effect(self, effect):
        self.effects.append(effect)

    def release(self):
        self.effects.append("released")

    def acquire(self):
        self.effects.append("acquired")

    def close(self):
        self.closed = True


def test_run_plays_effects_and_handles_taps(books_dir, tmp_path):
    ctx = Context(300, 400, books_dir, ProgressStore(tmp_path / "p.json"))
    device = FakeDevice([
        Tap(150, 44 + 46 + 10),  # tap the second book in the library
        Tap(290, 200),           # right third of the page: next page
        Tap(10, 200),            # left third: previous page
        Tap(150, 200),           # middle: menu
        Button.B,                # close the menu
    ])
    run(device, ctx)
    assert device.closed
    assert device.effects == [Effect.STARTUP, Effect.OPEN_BOOK, Effect.PAGE, Effect.PAGE,
                              Effect.SELECT, Effect.BACK]
    assert len(device.frames) == 6
    assert ctx.progress.last_book == "b.epub"


def test_finishing_a_book_catches_it(books_dir, tmp_path):
    state = tmp_path / "p.json"
    ctx = Context(300, 400, books_dir, ProgressStore(state))
    reader = ReaderScreen(ctx, "a.epub", dict(ctx.books())["a.epub"])
    for _ in range(len(reader.pages(0)) + 2):
        reader.handle(Button.RIGHT)
    effects = ctx.take_effects()
    assert effects.count(Effect.CAUGHT) == 1, "only the first time"
    assert ProgressStore(state).is_finished("a.epub")

    library = reader.handle(Button.B)
    assert isinstance(library, LibraryScreen)
    library.render()  # draws a caught Pokéball for a.epub, none for b.epub


def test_koreader_is_launched_from_the_library_and_the_book_menu(books_dir, tmp_path):
    marker = tmp_path / "runs.txt"
    koreader = [sys.executable, "-c", "import sys; open(sys.argv[1], 'a').write('ran ')", str(marker)]
    ctx = Context(300, 400, books_dir, ProgressStore(tmp_path / "p.json"), koreader=koreader)
    device = FakeDevice([
        Button.B, Button.A,             # library: B menu -> KOReader
        Button.A,                       # open the first book
        Button.A, Button.DOWN, Button.DOWN, Button.A,  # book menu: 3rd item is KOReader
        Button.RIGHT,                   # still in the book afterwards
    ])
    run(device, ctx)
    assert marker.read_text() == "ran ran "
    assert device.effects.count("released") == device.effects.count("acquired") == 2
    assert ctx.progress.last_book == "a.epub"


def test_library_b_does_nothing_without_koreader(books_dir, tmp_path):
    ctx = Context(300, 400, books_dir, ProgressStore(tmp_path / "p.json"))
    library = LibraryScreen(ctx)
    assert library.handle(Button.B) is library
    ctx.koreader = ["x"]
    assert isinstance(library.handle(Button.B), MenuScreen)


def test_missing_koreader_command_comes_back(books_dir, tmp_path, capsys):
    ctx = Context(300, 400, books_dir, ProgressStore(tmp_path / "p.json"),
                  koreader=[str(tmp_path / "no-such-koreader")])
    device = FakeDevice([Button.B, Button.A, Button.DOWN])
    run(device, ctx)
    assert "Could not start" in capsys.readouterr().err
    assert device.effects.count("acquired") == 1
