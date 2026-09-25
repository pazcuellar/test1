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
            manifest = {item.get("id"): item.get("href")
                        for item in opf.find("opf:manifest", NS)}
            self.chapter_files = [
                posixpath.normpath(posixpath.join(base, unquote(manifest[ref.get("idref")])))
                for ref in opf.find("opf:spine", NS)
                if ref.get("idref") in manifest and ref.get("linear") != "no"
            ]
        except (OSError, KeyError, AttributeError, TypeError,
                zipfile.BadZipFile, ElementTree.ParseError) as e:
            raise EpubError(f"{self.path.name}: {e}") from e

        self.title = _text(opf.find(".//dc:title", NS)) or self.path.stem
        self.author = _text(opf.find(".//dc:creator", NS))
        self._chapters: dict[int, list[Block]] = {}

    def chapter(self, index: int) -> list[Block]:
        """The text blocks of one chapter, parsed on first use."""
        if index not in self._chapters:
            try:
                with zipfile.ZipFile(self.path) as z:
                    html = z.read(self.chapter_files[index]).decode("utf-8", errors="replace")
            except KeyError:
                html = ""  # spine entry points at a missing file
            parser = _TextExtractor()
            parser.feed(html)
            parser.close()
            self._chapters[index] = parser.blocks
        return self._chapters[index]


def _text(element) -> str:
    return " ".join((element.text or "").split()) if element is not None else ""


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
