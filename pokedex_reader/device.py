"""The boundary between the reader and the hardware it runs on.

Everything the reader knows about the screen and the buttons goes through
`Device`. The laptop simulator and (later) the e-paper + GPIO version are
two implementations of it, so the rest of the code never changes.
"""

from __future__ import annotations

from enum import Enum

from PIL import Image

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


class DeviceClosed(Exception):
    """Raised by `wait_button` when the device is shutting down."""


class Device:
    """A screen plus the D-pad and A/B buttons."""

    width: int
    height: int

    def show(self, image: Image.Image) -> None:
        """Display a full frame. `image` is mode "L", `width` x `height`."""
        raise NotImplementedError

    def wait_button(self) -> Button:
        """Block until a button is pressed. Raises `DeviceClosed` on quit."""
        raise NotImplementedError

    def release(self) -> None:
        """Hand the screen and buttons to another program (e.g. KOReader)."""
        raise NotImplementedError

    def acquire(self) -> None:
        """Take the screen and buttons back after `release`."""
        raise NotImplementedError

    def close(self) -> None:
        pass
