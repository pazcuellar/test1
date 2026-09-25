"""Chimes and cover-light animations, described as data.

Screens ask for an `Effect`; each device plays it its own way: the simulator
through the laptop speakers and a drawing of the cover, the Pi through a
buzzer and the LEDs. Both read the same notes and light curves from here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Effect(Enum):
    STARTUP = "startup"
    SELECT = "select"
    BACK = "back"
    OPEN_BOOK = "open_book"
    PAGE = "page"
    CAUGHT = "caught"  # finished a book


# Notes as (frequency in Hz, length in ms). 0 Hz is a rest.
C6, E6, G6, A6, C7, E7, G7 = 1047, 1319, 1568, 1760, 2093, 2637, 3136
CHIMES: dict[Effect, list[tuple[int, int]]] = {
    Effect.STARTUP: [(C6, 70), (E6, 70), (G6, 70), (C7, 160)],
    Effect.SELECT: [(G7, 35)],
    Effect.BACK: [(G6, 35)],
    Effect.OPEN_BOOK: [(G6, 60), (C7, 110)],
    Effect.PAGE: [],  # silent: a chime on every page would get old fast
    Effect.CAUGHT: [(C7, 90), (0, 30), (C7, 90), (0, 30), (C7, 90), (A6, 90), (E7, 320)],
}


@dataclass(frozen=True)
class Lights:
    """Brightness of each cover light, 0.0 (off) to 1.0 (full)."""

    lens: float = 0.0
    red: float = 0.0
    yellow: float = 0.0
    green: float = 0.0


IDLE = Lights(lens=0.25)  # the lens glows softly while the reader is on

DURATIONS = {
    Effect.STARTUP: 0.9,
    Effect.SELECT: 0.25,
    Effect.BACK: 0.25,
    Effect.OPEN_BOOK: 0.5,
    Effect.PAGE: 0.15,
    Effect.CAUGHT: 1.5,
}


def lights_at(effect: Effect, t: float) -> Lights:
    """The cover lights `t` seconds into `effect`. After it ends: IDLE."""
    duration = DURATIONS[effect]
    if t >= duration:
        return IDLE
    fade = 1 - t / duration  # 1 -> 0 over the effect
    idle = IDLE.lens
    if effect == Effect.STARTUP:
        # The lens wakes up, then the three small lights blink in turn.
        step = int(t / duration * 6)
        return Lights(lens=min(1.0, t / (duration / 2)) if t < duration / 2 else idle + (1 - idle) * fade * 2,
                      red=1.0 if step == 3 else 0.0,
                      yellow=1.0 if step == 4 else 0.0,
                      green=1.0 if step == 5 else 0.0)
    if effect in (Effect.SELECT, Effect.OPEN_BOOK):
        return Lights(lens=idle + (1 - idle) * fade)
    if effect == Effect.BACK:
        return Lights(lens=idle * (1 - fade))
    if effect == Effect.PAGE:
        return Lights(lens=idle + 0.35 * fade)
    # CAUGHT: the small lights chase each other three times, lens pulsing.
    step = int(t / duration * 9) % 3
    pulse = 1.0 if int(t / duration * 6) % 2 == 0 else idle
    return Lights(lens=pulse, red=float(step == 0), yellow=float(step == 1), green=float(step == 2))
