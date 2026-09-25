# Pokédex Reader

A DIY e-ink book reader shaped like the Gen 1 Kanto Pokédex.
See [PLAN.md](PLAN.md) for the design and [SHOPPING_LIST.md](SHOPPING_LIST.md) for parts.

## Run it on your laptop

Needs Python 3.10 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[sim,dev]"
python -m pokedex_reader --books ~/Books
```

Put `.epub` files in the books folder. Free public-domain books are at
[Project Gutenberg](https://www.gutenberg.org) and [Standard Ebooks](https://standardebooks.org).

A window stands in for the device: a 300×400 screen drawn in the e-paper's 4 gray levels, plus the cover lights above it.

| Key | Button | Library | Reading | Menu | Contents |
|---|---|---|---|---|---|
| ↑ ↓ | D-pad | choose a book | — | choose an item | choose a chapter |
| ← → | D-pad | — | previous / next page | text size smaller / bigger | — |
| Z or Enter | A | open book | open the menu | select | go to chapter |
| X, Backspace or Esc | B | — | back to the library | close | back to the page |
| Q | — | quit | quit | quit | quit |

**Mouse clicks are taps** on the touchscreen:
- Library: tap a book to open it.
- Reading: tap the left third to go back a page, the right third to go forward, the middle for the menu.
- Menu: tap an item. On Text size, tap the left side for smaller text and the right side for bigger. Tap the page above the menu to close it.
- Contents: tap a chapter.

The red strip above the screen is the **cover**: the blue lens and the red, yellow and
green lights animate, and chimes play through your speakers. In the library, a Pokéball
outline marks books you've opened (**seen**). A filled Pokéball marks books you've
finished (**caught**); you get a jingle when you press next on the last page.

The menu has **Text size** (5 sizes, remembered for all books), **Contents**
(the book's table of contents) and **Library**.

Your page in every book is saved in `~/.pokedex-reader/progress.json`. If you quit
while reading, the reader reopens that book at your page next time, the way it
will when you open the lid.

Options: `--landscape` (400×300), `--scale 3` (bigger window), `--state FILE`.

## Tests

```bash
pytest
```

## Code map

| File | What it does |
|---|---|
| `pokedex_reader/device.py` | The interface for the screen, buttons, touch, buzzer and cover lights. The only part that changes on the Pi. |
| `pokedex_reader/simulator.py` | The laptop version of the device (pygame window, keyboard, mouse, speakers). |
| `pokedex_reader/epub.py` | Opens EPUBs: title, author, chapters as text blocks. |
| `pokedex_reader/layout.py` | Wraps text into lines and pages. |
| `pokedex_reader/screens.py` | The Pokédex library screen and the reading screen. |
| `pokedex_reader/progress.py` | Saves your place in each book. |
| `pokedex_reader/effects.py` | Chime notes and cover-light animations, shared by the simulator and the Pi. |
| `pokedex_reader/app.py` | The main loop. |
