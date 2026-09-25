import zipfile
from pathlib import Path

import pytest

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>"""


def make_epub(path: Path, title: str, author: str, chapters: list[str],
              toc: str | None = None, toc_titles: list[str] | None = None) -> Path:
    """Write a minimal EPUB whose chapters have the given <body> contents.

    `toc` adds a table of contents: "nav" (EPUB 3) or "ncx" (EPUB 2), with
    one entry per chapter titled from `toc_titles`.
    """
    items = "".join(
        f'<item id="c{i}" href="text/ch%20{i}.xhtml" media-type="application/xhtml+xml"/>'
        for i in range(len(chapters)))
    titles = toc_titles or [f"Chapter {i}" for i in range(len(chapters))]
    files = {}
    spine_attr = ""
    if toc == "nav":
        items += '<item id="nav" href="nav.xhtml" properties="nav" media-type="application/xhtml+xml"/>'
        links = "".join(f'<li><a href="text/ch%20{i}.xhtml#top">{t}</a></li>' for i, t in enumerate(titles))
        files["OEBPS/nav.xhtml"] = (
            '<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops"><body>'
            f'<nav epub:type="landmarks"><ol><li><a href="text/ch%200.xhtml">Cover</a></li></ol></nav>'
            f'<nav epub:type="toc"><h1>Contents</h1><ol>{links}</ol></nav></body></html>')
    elif toc == "ncx":
        items += '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>'
        spine_attr = ' toc="ncx"'
        points = "".join(
            f'<navPoint id="p{i}"><navLabel><text>{t}</text></navLabel><content src="text/ch%20{i}.xhtml"/></navPoint>'
            for i, t in enumerate(titles))
        files["OEBPS/toc.ncx"] = (
            f'<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><navMap>{points}</navMap></ncx>')
    spine = "".join(f'<itemref idref="c{i}"/>' for i in range(len(chapters)))
    opf = f"""<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{title}</dc:title><dc:creator>{author}</dc:creator>
  </metadata>
  <manifest>{items}</manifest>
  <spine{spine_attr}>{spine}</spine>
</package>"""
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "application/epub+zip")
        z.writestr("META-INF/container.xml", CONTAINER)
        z.writestr("OEBPS/content.opf", opf)
        for name, content in files.items():
            z.writestr(name, content)
        for i, body in enumerate(chapters):
            z.writestr(f"OEBPS/text/ch {i}.xhtml",
                       f'<?xml version="1.0"?><html xmlns="http://www.w3.org/1999/xhtml">'
                       f"<head><title>ignored</title><style>p {{}}</style></head>"
                       f"<body>{body}</body></html>")
    return path


def long_chapter(heading: str, paragraphs: int = 30) -> str:
    para = "<p>" + " ".join(f"word{n}" for n in range(60)) + "</p>"
    return f"<h1>{heading}</h1>" + para * paragraphs


@pytest.fixture
def books_dir(tmp_path):
    folder = tmp_path / "books"
    folder.mkdir()
    make_epub(folder / "b.epub", "Beta Book", "Bee Author",
              ['<img src="cover.jpg"/>', long_chapter("One"), long_chapter("Two")])
    make_epub(folder / "a.epub", "Alpha Book", "Ay Author", [long_chapter("Only")])
    (folder / "broken.epub").write_text("not a zip")
    return folder
