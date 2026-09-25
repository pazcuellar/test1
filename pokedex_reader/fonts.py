"""Finding fonts on Raspberry Pi OS, Linux, macOS and Windows."""

from __future__ import annotations

from pathlib import Path

from PIL import ImageFont

SERIF = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    "/System/Library/Fonts/Supplemental/Georgia.ttf",
    "C:/Windows/Fonts/georgia.ttf",
]
SERIF_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "C:/Windows/Fonts/georgiab.ttf",
]
SANS_BOLD = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
SANS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def load(candidates: list[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)  # Pillow's built-in font
