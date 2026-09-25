from pokedex_reader import fonts
from pokedex_reader.epub import Block
from pokedex_reader.layout import Position, TextStyle, page_index, paginate, wrap

FONT = fonts.load(fonts.SERIF, 17)
STYLE = TextStyle(body=FONT, heading=fonts.load(fonts.SERIF_BOLD, 21), width=268, height=340)


def test_wrap_keeps_every_word_within_width():
    words = ("the quick brown fox jumps over the lazy dog " * 20).split()
    lines = list(wrap(words, FONT, 200))
    assert " ".join(text for _, text in lines).split() == words
    assert all(FONT.getlength(text) <= 200 for _, text in lines)
    # Each line knows the index of its first word.
    for first, text in lines:
        assert text.split()[0] == words[first]


def test_wrap_cuts_words_wider_than_the_line():
    lines = list(wrap(["x" * 200, "end"], FONT, 100))
    assert "".join(text for _, text in lines).replace(" ", "") == "x" * 200 + "end"
    assert all(FONT.getlength(text) <= 100 for _, text in lines)


def test_paginate_fits_pages_and_keeps_all_text():
    blocks = [Block("heading", "Title")] + [
        Block("para", " ".join(f"w{b}-{n}" for n in range(50))) for b in range(20)]
    pages = paginate(blocks, 3, STYLE)
    assert len(pages) > 1
    ascent, descent = FONT.getmetrics()
    for page in pages:
        assert page.start.chapter == 3
        assert page.lines[-1].y + ascent + descent <= STYLE.height
    words = [w for page in pages for line in page.lines for w in line.text.split()]
    assert words == [w for block in blocks for w in block.text.split()]
    assert pages[0].start == Position(3, 0, 0)
    assert pages[1].start > pages[0].start


def test_empty_chapter_has_no_pages():
    assert paginate([], 0, STYLE) == []


def test_page_index_finds_the_page_holding_a_position():
    blocks = [Block("para", " ".join(f"w{n}" for n in range(2000)))]
    pages = paginate(blocks, 0, STYLE)
    assert page_index(pages, Position(0, 0, 0)) == 0
    for i, page in enumerate(pages):
        assert page_index(pages, page.start) == i
    # A position in the middle of page 2 maps to page 2.
    middle = Position(0, 0, (pages[2].start.word + pages[3].start.word) // 2)
    assert page_index(pages, middle) == 2
