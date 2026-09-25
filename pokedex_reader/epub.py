"""Reading EPUB files into plain-text blocks.

An EPUB is a zip file: `META-INF/container.xml` points at an OPF file, which
lists the book's metadata and its "spine" (the chapter files in reading
order). Chapters are XHTML; we keep only headings and paragraphs of text.
"""

from __future__ import annotations

import posixpath
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree

NS = {
    "c": "urn:oasis:names:tc:opendocument:xmlns:container",
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}
NCX = {"n": "http://www.daisy.org/z3986/2005/ncx/"}

HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
BLOCKS = {"p", "div", "li", "blockquote", "pre", "tr", "dt", "dd", "br",
          "section", "article", "figcaption"}
SKIPPED = {"head", "script", "style"}


class EpubError(Exception):
    """The file is not a readable EPUB."""


@dataclass(frozen=True)
class Block:
    kind: str  # "heading" or "para"
    text: str


class Book:
    def __init__(self, path: Path):
        self.path = Path(path)
        try:
            with zipfile.ZipFile(self.path) as z:
                container = ElementTree.fromstring(z.read("META-INF/container.xml"))
                opf_path = container.find(".//c:rootfile", NS).get("full-path")
                opf = ElementTree.fromstring(z.read(opf_path))
            base = posixpath.dirname(opf_path)
            items = list(opf.find("opf:manifest", NS))
            manifest = {item.get("id"): _join(base, item.get("href")) for item in items}
            spine = opf.find("opf:spine", NS)
            self.chapter_files = [
                manifest[ref.get("idref")] for ref in spine
                if ref.get("idref") in manifest and ref.get("linear") != "no"
            ]
            # EPUB 3 marks its table of contents with properties="nav";
            # EPUB 2 points at an NCX file from the spine.
            self._nav_file = next((manifest[item.get("id")] for item in items
                                   if "nav" in (item.get("properties") or "").split()), None)
            self._ncx_file = manifest.get(spine.get("toc"))
        except (OSError, KeyError, AttributeError, TypeError,
                zipfile.BadZipFile, ElementTree.ParseError) as e:
            raise EpubError(f"{self.path.name}: {e}") from e

        self.title = _text(opf.find(".//dc:title", NS)) or self.path.stem
        self.author = _text(opf.find(".//dc:creator", NS))
        self._chapters: dict[int, list[Block]] = {}
        self._toc: list[TocEntry] | None = None

    def chapter(self, index: int) -> list[Block]:
        """The text blocks of one chapter, parsed on first use."""
        if index not in self._chapters:
            parser = _TextExtractor()
            parser.feed(self._read(self.chapter_files[index]))
            parser.close()
            self._chapters[index] = parser.blocks
        return self._chapters[index]

    def toc(self) -> list[TocEntry]:
        """The book's table of contents, or one entry per chapter with text."""
        if self._toc is None:
            self._toc = self._read_toc() or [
                TocEntry(_chapter_title(blocks), i)
                for i in range(len(self.chapter_files)) if (blocks := self.chapter(i))
            ]
        return self._toc

    def _read_toc(self) -> list[TocEntry]:
        if self._nav_file:
            parser = _NavExtractor()
            parser.feed(self._read(self._nav_file))
            parser.close()
            links, base = parser.links, posixpath.dirname(self._nav_file)
        elif self._ncx_file:
            try:
                ncx = ElementTree.fromstring(self._read(self._ncx_file))
            except ElementTree.ParseError:
                return []
            links = [(_text(point.find("n:navLabel/n:text", NCX)),
                      point.find("n:content", NCX).get("src", ""))
                     for point in ncx.iter(f"{{{NCX['n']}}}navPoint")
                     if point.find("n:content", NCX) is not None]
            base = posixpath.dirname(self._ncx_file)
        else:
            return []
        entries = []
        for title, href in links:
            file = _join(base, href.split("#")[0])
            if title and file in self.chapter_files:
                entry = TocEntry(title, self.chapter_files.index(file))
                if entry not in entries:
                    entries.append(entry)
        return entries

    def _read(self, name: str) -> str:
        try:
            with zipfile.ZipFile(self.path) as z:
                return z.read(name).decode("utf-8", errors="replace")
        except KeyError:
            return ""  # the book points at a file it doesn't contain


@dataclass(frozen=True)
class TocEntry:
    title: str
    chapter: int


def _join(base: str, href: str) -> str:
    return posixpath.normpath(posixpath.join(base, unquote(href)))


def _text(element) -> str:
    return " ".join((element.text or "").split()) if element is not None else ""


def _chapter_title(blocks: list[Block]) -> str:
    """A name for a chapter in a book without a table of contents."""
    for block in blocks:
        if block.kind == "heading":
            return block.text
    words = blocks[0].text.split()
    return " ".join(words[:6]) + ("\u2026" if len(words) > 6 else "")


class _NavExtractor(HTMLParser):
    """Collects (title, href) of the links inside <nav epub:type="toc">."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self._nav_depth = 0  # >0 while inside the toc <nav>
        self._href: str | None = None
        self._title: list[str] = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and (self._nav_depth or "toc" in (attrs.get("epub:type") or "").split()):
            self._nav_depth += 1
        elif tag == "a" and self._nav_depth:
            self._href, self._title = attrs.get("href") or "", []

    def handle_endtag(self, tag):
        if tag == "nav" and self._nav_depth:
            self._nav_depth -= 1
        elif tag == "a" and self._href is not None:
            self.links.append((" ".join("".join(self._title).split()), self._href))
            self._href = None

    def handle_data(self, data):
        if self._href is not None:
            self._title.append(data)


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self._buffer: list[str] = []
        self._kind = "para"
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in SKIPPED:
            self._skip_depth += 1
        elif tag in HEADINGS:
            self._flush()
            self._kind = "heading"
        elif tag in BLOCKS:
            self._flush()

    def handle_endtag(self, tag):
        if tag in SKIPPED:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag in HEADINGS:
            self._flush()
            self._kind = "para"
        elif tag in BLOCKS:
            self._flush()

    def handle_data(self, data):
        if not self._skip_depth:
            self._buffer.append(data)

    def close(self):
        super().close()
        self._flush()

    def _flush(self):
        text = " ".join("".join(self._buffer).split())
        self._buffer = []
        if text:
            self.blocks.append(Block(self._kind, text))
