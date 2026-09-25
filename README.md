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

A 300×400 window stands in for the e-paper screen, drawn in its 4 gray levels.

| Key | Button | Library | Reading |
|---|---|---|---|
| ↑ ↓ | D-pad | choose a book | — |
| ← → | D-pad | — | previous / next page |
| Z or Enter | A | open book | — |
| X, Backspace or Esc | B | — | back to the library |
| Q | — | quit | quit |

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
| `pokedex_reader/device.py` | The screen + buttons interface. The only part that changes on the Pi. |
| `pokedex_reader/simulator.py` | The laptop version of the device (pygame window + keyboard). |
| `pokedex_reader/epub.py` | Opens EPUBs: title, author, chapters as text blocks. |
| `pokedex_reader/layout.py` | Wraps text into lines and pages. |
| `pokedex_reader/screens.py` | The Pokédex library screen and the reading screen. |
| `pokedex_reader/progress.py` | Saves your place in each book. |
| `pokedex_reader/app.py` | The main loop. |
