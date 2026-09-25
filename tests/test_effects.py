import pytest

from pokedex_reader.effects import CHIMES, DURATIONS, IDLE, Effect, lights_at


@pytest.mark.parametrize("effect", list(Effect))
def test_every_effect_has_a_chime_and_ends_idle(effect):
    assert effect in CHIMES
    assert lights_at(effect, DURATIONS[effect]) == IDLE
    for step in range(50):
        lights = lights_at(effect, DURATIONS[effect] * step / 50)
        assert all(0.0 <= v <= 1.0 for v in (lights.lens, lights.red, lights.yellow, lights.green))


def test_caught_lights_chase():
    lit = {name for step in range(90)
           for name in ("red", "yellow", "green")
           if getattr(lights_at(Effect.CAUGHT, DURATIONS[Effect.CAUGHT] * step / 90), name)}
    assert lit == {"red", "yellow", "green"}
