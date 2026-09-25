"""The main loop: wait for a button or tap, update the screen, repeat."""

from __future__ import annotations

from .device import Button, Device, DeviceClosed
from .effects import Effect
from .screens import Context, start_screen


def run(device: Device, ctx: Context) -> None:
    screen = start_screen(ctx)
    try:
        device.effect(Effect.STARTUP)
        device.show(screen.render())
        while True:
            event = device.wait_input()
            screen = screen.handle(event) if isinstance(event, Button) else screen.tap(event.x, event.y)
            # Chimes first: the e-paper takes a moment to redraw.
            for effect in ctx.take_effects():
                device.effect(effect)
            device.show(screen.render())
    except DeviceClosed:
        pass
    finally:
        device.close()
