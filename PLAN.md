# Pokédex E-Reader — Plan

A DIY e-ink book reader in the shape of the Gen 1 (Kanto) Pokédex.
Decisions below were settled in a `/grill-me` session on 2026-09-25.

## Goals

- **Learn** electronics, embedded Linux and Python by building it.
- **Own it**: no store, no account, fully personal, Pokédex-themed.
- Built for one user (me). Rough edges are acceptable.
- Budget: **~$200 including shipping** (estimate: $145–185 + shipping).
- Time: **a few weekends** to a first working version.

## Hardware

| Area | Decision |
|---|---|
| Board | **Raspberry Pi Zero 2 W** (small, cheap, low power, can act as a USB drive) |
| Screen | **Good Display GDEY042T81-FT02** — 4.2", 400×300, 4 gray levels, SPI, built-in **frontlight** and capacitive touch. Connected via a **DESPI-C02** adapter. |
| Formats | **EPUB only.** PDFs are out of scope at 400×300. |
| Frontlight | Brightness steps, remembered across shutdowns. Driven by PWM (GPIO12, as in piEreader). |
| Input | **D-pad + A/B**: left/right = page, up/down = menus, A = select, B = back. Touch left unconnected until the "fun extras" stage. |
| Books | Copied over **USB** — the Pi presents itself as a USB drive (mass-storage gadget). While plugged in, the reader can't open books. |
| Lid | Magnet in the lid + **reed switch**. Close → idle (light off); after **30 min** idle → full shutdown. Open → wake, or boot if shut down. |
| Off switch | Hidden slide switch on the battery lead (hard off). |
| Cover lights | Blue lens + small lights as **status**: on/waking, charging, battery low, USB transfer. Animations defined in `effects.py`. |
| Chimes | Passive piezo buzzer on GPIO13 (PWM), playing the notes in `effects.py`. |

### Power — built in stages

- **Stage 1:** Adafruit PowerBoost 1000C (charge while running) + the largest flat LiPo that fits the battery half + simple power switch. Charging via the PowerBoost's own port (separate from data).
- **Stage 2:**
  - Latching power switch + reed switch so opening the lid powers on from **full off**; the Pi cuts its own power after `shutdown` (`dtoverlay=gpio-poweroff`).
  - **One USB-C port** for charging *and* books: USB-C breakout with 5.1 kΩ CC pull-downs; VBUS → charger input only; D+/D−/GND → the Pi's data micro-USB; the Pi-side VBUS left unconnected (avoids back-feeding the host).

Estimated draw: Pi idle ~0.4–0.5 W, reading ~0.6–1.2 W, plus frontlight.
A halted (not powered-off) Zero 2 W still draws ~45 mA, which is why stage 2 cuts power entirely.

### Frontlight driver — open question

It's unclear whether the panel's 7 LEDs are in **parallel** (~3 V) or **series** (~20 V).

1. Ask Good Display / the seller for the datasheet when ordering.
2. On arrival, measure with the multimeter.
3. Parallel → logic-level MOSFET (e.g. AO3400) + resistor + PWM.
   Series → buy a ready-made PWM-dimmable LED boost driver board.

## Case

- **Style:** Gen 1 Kanto **red clamshell**.
- **Inner layout:** screen on top with the D-pad and A/B below it (Game Boy style) on one half; the other half holds battery + electronics behind a decorative panel. Each half ≈ 11 × 15 cm.
- **Hinge:** folds fully back (**360°**) for one-handed reading. Fallback: a simple 180° hinge for version 1.
- **Cover:** blue lens + small status lights.
- **Design workflow:** remix an existing Kanto Pokédex model (Printables/Thingiverse), then model the precise parts (screen window, D-pad, board/battery mounts, hinge) in **Onshape or Fusion**.
- **Printing:** test prints at a **makerspace/library** in whatever colour is available; final print from a **printing service** (e.g. JLCPCB, Craftcloud) in coloured parts — red body, blue lens, dark D-pad. Painting is a possible later upgrade.

## Software

Written in **Python**. Own reader first; KOReader later.

### Version 1 (first working version)

1. Open an EPUB and show its text.
2. Turn pages back and forth with the D-pad.
3. Remember the current page per book across sleep and shutdown.
4. A library screen listing books, with Pokédex styling.

### Next

- Font size (high priority at 400×300).
- Chapter list / table of contents.
- Full theme: library as Pokédex entries (#001 Dune…), startup chime, lens animations, touch.
- **KOReader** as an "app" launched from the reader's menu; exiting it returns home.
- Out of scope for now: images in books, bookmarks, search, dictionary.

### Architecture rules decided now

- **Display and input sit behind one interface**, with two implementations:
  - a **desktop simulator**: a 400×300 window, with arrow keys / Z / X standing in for the D-pad and A/B;
  - the **e-paper + GPIO** version on the Pi.
- The reader must be able to **release the screen and input** so another program (KOReader) can take over, then reclaim them.

## Order of work

1. Order parts now (see [SHOPPING_LIST.md](SHOPPING_LIST.md)).
2. While they ship: build the version 1 reader on the laptop using the simulator.
3. When parts arrive: measure the frontlight, wire screen + buttons + light, and port the display/input layer.
4. Test prints of the case; iterate on fit.
5. Power stage 1 → a device you can read with.
6. Power stage 2, cover status lights, final printed case.
7. Font size, chapters, theme extras, touch, KOReader.

## Known risks

- Screen **price and stock** are unconfirmed; the store lists "request a quote".
- **Frontlight wiring** is unknown until the datasheet or a measurement.
- **Single USB-C port** wiring has no complete guide; it's careful custom work.
- The **360° hinge** is the hardest print.
- **KOReader** has no existing port for this screen on a Pi; running it will need porting work.
- The Zero 2 W's speed has only been judged for a simple text reader, not measured.

## References

- piEreader (abandoned but has the frontlight and board wiring): https://gitlab.com/guyjeangilles/piereader
- Pi Zero USB gadget setup: https://gist.github.com/gbaman/50b6cca61dd1c3f88f41
- DIY light guides (if ever needed): https://hackaday.com/2023/03/13/a-hackers-introduction-to-diy-light-guide-plates/
