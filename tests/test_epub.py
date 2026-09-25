import pytest

from pokedex_reader.epub import Block, Book, EpubError

from .conftest import make_epub


def test_reads_metadata_and_spine(tmp_path):
    book = Book(make_epub(tmp_path / "x.epub", "My Title", "Me", ["<p>a</p>", "<p>b</p>"]))
    assert book.title == "My Title"
    assert book.author == "Me"
    assert book.chapter_files == ["OEBPS/text/ch 0.xhtml", "OEBPS/text/ch 1.xhtml"]


def test_chapter_text_blocks(tmp_path):
    body = ("<h2>Chapter  One</h2><p>Hello,\n   <em>brave</em> new world&#8212;&amp; more.</p>"
            "<script>ignored()</script><div><p>Second</p> tail</div><p>line<br/>break</p>")
    book = Book(make_epub(tmp_path / "x.epub", "T", "A", [body]))
    assert book.chapter(0) == [
        Block("heading", "Chapter One"),
        Block("para", "Hello, brave new world—& more."),
        Block("para", "Second"),
        Block("para", "tail"),
        Block("para", "line"),
        Block("para", "break"),
    ]


def test_image_only_chapter_has_no_blocks(tmp_path):
    book = Book(make_epub(tmp_path / "x.epub", "T", "A", ['<img src="c.jpg"/>']))
    assert book.chapter(0) == []


def test_title_falls_back_to_file_name(tmp_path):
    book = Book(make_epub(tmp_path / "fallback.epub", "", "", ["<p>a</p>"]))
    assert book.title == "fallback"


def test_broken_file_raises_epub_error(tmp_path):
    path = tmp_path / "bad.epub"
    path.write_text("not a zip")
    with pytest.raises(EpubError):
        Book(path)


@pytest.mark.parametrize("kind", ["nav", "ncx"])
def test_table_of_contents(tmp_path, kind):
    book = Book(make_epub(tmp_path / "x.epub", "T", "A", ["<p>a</p>", "<p>b</p>", "<p>c</p>"],
                          toc=kind, toc_titles=["Start", "Middle", "End"]))
    assert [(e.title, e.chapter) for e in book.toc()] == [("Start", 0), ("Middle", 1), ("End", 2)]


def test_contents_without_a_toc_uses_headings_or_first_words(tmp_path):
    book = Book(make_epub(tmp_path / "x.epub", "T", "A", [
        '<img src="cover.jpg"/>',
        "<h2>The Beginning</h2><p>text</p>",
        "<p>one two three four five six seven eight</p>",
    ]))
    assert [(e.title, e.chapter) for e in book.toc()] == [
        ("The Beginning", 1), ("one two three four five six…", 2)]
