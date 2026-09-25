"""The main loop: show the current screen, wait for a button, repeat."""

from __future__ import annotations

from .device import Device, DeviceClosed
from .screens import Context, start_screen


def run(device: Device, ctx: Context) -> None:
    screen = start_screen(ctx)
    try:
        while True:
            device.show(screen.render())
            screen = screen.handle(device.wait_button())
    except DeviceClosed:
        pass
    finally:
        device.close()
