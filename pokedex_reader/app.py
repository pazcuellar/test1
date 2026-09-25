"""The main loop: wait for a button or tap, update the screen, repeat."""

from __future__ import annotations

import subprocess
import sys

from .device import Button, Device, DeviceClosed
from .effects import Effect
from .screens import Context, Launch, start_screen


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
            if isinstance(screen, Launch):
                screen = launch(device, screen)
            device.show(screen.render())
    except DeviceClosed:
        pass
    finally:
        device.close()


def launch(device: Device, request: Launch):
    """Hand the device to another program until it exits."""
    device.release()
    try:
        subprocess.run(request.command, check=False)
    except OSError as e:
        print(f"Could not start {request.command[0]}: {e}", file=sys.stderr)
    finally:
        device.acquire()
    return request.return_to
