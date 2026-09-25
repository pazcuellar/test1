"""A window on the laptop that stands in for the whole device.

The cover lights (blue lens, red/yellow/green) are drawn above the screen,
chimes play through the speakers, and mouse clicks are taps.

Keys: arrows = D-pad, Z or Enter = A, X / Backspace / Esc = B, Q = quit.
"""

from __future__ import annotations

import math
import time
from array import array

import pygame
from PIL import Image

from .device import Button, Device, DeviceClosed, Input, Tap
from .effects import CHIMES, IDLE, Effect, Lights, lights_at

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

COVER = 36  # height of the cover-lights strip, in screen pixels
CASE_RED = (200, 30, 40)
LIGHT_COLORS = {"lens": (60, 160, 255), "red": (255, 60, 60),
                "yellow": (255, 220, 60), "green": (80, 230, 90)}
SAMPLE_RATE = 22050


def _channel(c: int) -> list[int]:
    """Lookup table snapping any gray to the nearest of the 4 panel levels."""
    return [PAPER[min(3, round(v / 85))][c] for v in range(256)]


LUTS = [_channel(c) for c in range(3)]


def _tone(notes: list[tuple[int, int]]) -> bytes:
    """Render notes as 16-bit mono sine waves with short fades (no clicks)."""
    samples = array("h")
    for freq, ms in notes:
        n = SAMPLE_RATE * ms // 1000
        fade = min(n // 4, SAMPLE_RATE // 200)
        for i in range(n):
            level = min(1.0, i / fade, (n - i) / fade) if fade else 1.0
            value = math.sin(2 * math.pi * freq * i / SAMPLE_RATE) if freq else 0.0
            samples.append(int(9000 * level * value))
    return samples.tobytes()


class Simulator(Device):
    def __init__(self, width: int, height: int, scale: int = 2):
        self.width, self.height, self.scale = width, height, scale
        pygame.display.init()
        self._window = pygame.display.set_mode((width * scale, (height + COVER) * scale))
        pygame.display.set_caption("Pokédex Reader (simulator)")
        self._frame: pygame.Surface | None = None
        self._effect: Effect | None = None
        self._effect_start = 0.0
        self._sounds = self._load_sounds()

    def _load_sounds(self) -> dict[Effect, pygame.mixer.Sound]:
        try:
            pygame.mixer.init(SAMPLE_RATE, -16, 1)
        except pygame.error:
            return {}  # no sound card: stay silent
        return {effect: pygame.mixer.Sound(buffer=_tone(notes))
                for effect, notes in CHIMES.items() if notes}

    def show(self, image: Image.Image) -> None:
        gray = image.convert("L")
        rgb = Image.merge("RGB", [gray.point(lut) for lut in LUTS])
        frame = pygame.image.frombytes(rgb.tobytes(), rgb.size, "RGB")
        self._frame = pygame.transform.scale(frame, (self.width * self.scale, self.height * self.scale))
        self._redraw()

    def effect(self, effect: Effect) -> None:
        self._effect, self._effect_start = effect, time.monotonic()
        if effect in self._sounds:
            self._sounds[effect].play()
        self._redraw()

    def _lights(self) -> Lights:
        if self._effect is None:
            return IDLE
        lights = lights_at(self._effect, time.monotonic() - self._effect_start)
        if lights == IDLE:
            self._effect = None
        return lights

    def _redraw(self) -> None:
        s = self.scale
        self._window.fill(CASE_RED, (0, 0, self.width * s, COVER * s))
        lights = self._lights()
        cy = COVER * s // 2
        self._draw_light((22 * s, cy), 13 * s, LIGHT_COLORS["lens"], lights.lens)
        for i, name in enumerate(("red", "yellow", "green")):
            self._draw_light(((46 + i * 14) * s, cy - 6 * s), 4 * s, LIGHT_COLORS[name], getattr(lights, name))
        if self._frame is not None:
            self._window.blit(self._frame, (0, COVER * s))
        pygame.display.flip()

    def _draw_light(self, center, radius, color, level: float) -> None:
        off = tuple(c // 5 for c in color)
        lit = tuple(round(o + (c - o) * level) for o, c in zip(off, color))
        pygame.draw.circle(self._window, (240, 240, 240), center, radius + max(2, radius // 6))
        pygame.draw.circle(self._window, lit, center, radius)

    def wait_input(self) -> Input:
        while True:
            # Animate at ~60 fps while an effect plays; otherwise just sleep.
            event = pygame.event.wait(16 if self._effect else 0)
            if self._effect:
                self._redraw()
            if event.type == pygame.QUIT:
                raise DeviceClosed
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    raise DeviceClosed
                if event.key in KEYS:
                    return KEYS[event.key]
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                x, y = event.pos[0] // self.scale, event.pos[1] // self.scale - COVER
                if 0 <= y < self.height:
                    return Tap(x, y)
            elif event.type in (pygame.WINDOWEXPOSED, pygame.VIDEOEXPOSE):
                self._redraw()

    def release(self) -> None:
        pygame.display.iconify()

    def acquire(self) -> None:
        self._redraw()

    def close(self) -> None:
        pygame.quit()
