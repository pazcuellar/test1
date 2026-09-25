"""The boundary between the reader and the hardware it runs on.

Everything the reader knows about the screen, buttons, touch, buzzer and
cover lights goes through `Device`. The laptop simulator and (later) the
e-paper + GPIO version are two implementations of it, so the rest of the
code never changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from PIL import Image

from .effects import Effect

# The e-paper panel shows 4 gray levels. Draw only with these.
BLACK = 0
DARK = 85
LIGHT = 170
WHITE = 255


class Button(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    A = "a"
    B = "b"


@dataclass(frozen=True)
class Tap:
    """A touch on the screen, in screen pixels."""

    x: int
    y: int


Input = Button | Tap


class DeviceClosed(Exception):
    """Raised by `wait_input` when the device is shutting down."""


class Device:
    """A screen plus the D-pad, A/B buttons, touch, buzzer and cover lights."""

    width: int
    height: int

    def show(self, image: Image.Image) -> None:
        """Display a full frame. `image` is mode "L", `width` x `height`."""
        raise NotImplementedError

    def wait_input(self) -> Input:
        """Block until a button press or a tap. Raises `DeviceClosed` on quit."""
        raise NotImplementedError

    def effect(self, effect: Effect) -> None:
        """Start a chime and cover-light animation. Returns immediately."""
        raise NotImplementedError

    def release(self) -> None:
        """Hand the screen and buttons to another program (e.g. KOReader)."""
        raise NotImplementedError

    def acquire(self) -> None:
        """Take the screen and buttons back after `release`."""
        raise NotImplementedError

    def close(self) -> None:
        pass
