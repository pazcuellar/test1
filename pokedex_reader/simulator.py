"""A window on the laptop that stands in for the e-paper screen and buttons.

Keys: arrows = D-pad, Z or Enter = A, X / Backspace / Esc = B, Q = quit.
"""

from __future__ import annotations

import pygame
from PIL import Image

from .device import Button, Device, DeviceClosed

KEYS = {
    pygame.K_UP: Button.UP,
    pygame.K_DOWN: Button.DOWN,
    pygame.K_LEFT: Button.LEFT,
    pygame.K_RIGHT: Button.RIGHT,
    pygame.K_z: Button.A,
    pygame.K_RETURN: Button.A,
    pygame.K_x: Button.B,
    pygame.K_BACKSPACE: Button.B,
    pygame.K_ESCAPE: Button.B,
}

# How the panel's 4 gray levels roughly look: dark ink on off-white paper.
PAPER = [(34, 34, 34), (98, 98, 94), (162, 162, 156), (230, 228, 220)]


def _channel(c: int) -> list[int]:
    """Lookup table snapping any gray to the nearest of the 4 panel levels."""
    return [PAPER[min(3, round(v / 85))][c] for v in range(256)]


LUTS = [_channel(c) for c in range(3)]


class Simulator(Device):
    def __init__(self, width: int, height: int, scale: int = 2):
        self.width, self.height, self.scale = width, height, scale
        pygame.display.init()  # no audio needed
        self._window = pygame.display.set_mode((width * scale, height * scale))
        pygame.display.set_caption("Pokédex Reader (simulator)")
        self._frame: pygame.Surface | None = None

    def show(self, image: Image.Image) -> None:
        gray = image.convert("L")
        rgb = Image.merge("RGB", [gray.point(lut) for lut in LUTS])
        frame = pygame.image.frombytes(rgb.tobytes(), rgb.size, "RGB")
        self._frame = pygame.transform.scale(frame, self._window.get_size())
        self._redraw()

    def _redraw(self) -> None:
        if self._frame is not None:
            self._window.blit(self._frame, (0, 0))
            pygame.display.flip()

    def wait_button(self) -> Button:
        while True:
            event = pygame.event.wait()
            if event.type == pygame.QUIT:
                raise DeviceClosed
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    raise DeviceClosed
                if event.key in KEYS:
                    return KEYS[event.key]
            elif event.type in (pygame.WINDOWEXPOSED, pygame.VIDEOEXPOSE):
                self._redraw()

    def release(self) -> None:
        pygame.display.iconify()

    def acquire(self) -> None:
        self._redraw()

    def close(self) -> None:
        pygame.quit()
