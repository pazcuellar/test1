# Shopping List

Prices are rough estimates in USD, without shipping. Budget ceiling: **~$200 including shipping**.
Links are given only where research found the product page; otherwise use the search terms.
Tools already owned: soldering iron, multimeter, wire strippers, screwdrivers.

## Order now (version 1 + power stage 1)

| # | Part | Search terms / link | ~Cost | Notes |
|---|---|---|---|---|
| 1 | **RasTech Raspberry Pi Zero 2 W kit**: board, mini-HDMI adapter, micro-USB OTG cable, heatsink, 40-pin header (not soldered) | "RasTech Raspberry Pi Zero 2 W kit" | $25–30 | Solder the header yourself (good practice). The HDMI adapter and OTG cable help with first setup. The heatsink is optional; it may not fit in the clamshell. No microSD card or power supply included. Copying books needs a normal micro-USB **data** cable, not the OTG one. |
| 2 | microSD card, 32 GB, reputable brand | "SanDisk 32GB microSD A1" | $8 | Not included in the Pi kit. |
| 3 | **Good Display 4.2" e-paper kit**: GDEY042T81-FT02 panel (400×300, front light, I²C touch) + adapter board + ESP32 demo kit | Good Display kit found on Amazon; other sellers: [buyepaper](https://www.buyepaper.com/products/42-inch-e-paper-display-fast-update-morochrome-spi-e-ink-with-touch-and-front-light-gdey042t81-ft02) · [Good Display](https://www.good-display.com/product/617.html) | $35–55 | Check the model name says GDEY042T81-FT02. **Ask for the datasheet** (front-light LEDs series or parallel? FPC contact counts). Use the ESP32 demo to check the panel works before wiring the Pi. Order it first: it takes the longest to arrive. |
| 4 | ~~Adapter board DESPI-C02~~ | — | $0 | **Included in the kit (#3).** |
| 5 | Adafruit **PowerBoost 1000C** | [adafruit.com/product/2465](https://www.adafruit.com/product/2465) | $20 | Charges while running. |
| 6 | Flat LiPo, 3.7 V, 3000–4000 mAh, **with protection circuit and JST-PH connector** | "3.7V 3000mAh LiPo JST PH protected" | $12–18 | Check its size against the battery half (~11 × 15 cm, thin). Match connector polarity to the PowerBoost. |
| 7 | Tactile buttons, 6×6 mm, assorted heights (for D-pad + A/B) | "6x6mm tactile switch assortment" | $3–5 | D-pad = 4 buttons under one printed cap. |
| 8 | Slide switch (SPDT, small) | "mini SPDT slide switch" | $1–2 | Stage 1 power switch; later the hidden hard-off. |
| 9 | Logic-level N-MOSFET (AO3400 or similar) + assorted resistors | "AO3400 SOT-23" or a through-hole "IRLZ44N"; "resistor kit" | $3–5 | For the frontlight **if** the LEDs are parallel. |
| 10 | 5 mm or 3 mm LEDs (blue, red, yellow, green) + resistors | "LED assortment 3mm 5mm" | $3 | Lens + status lights. |
| 11 | Wire, perfboard, female/male headers, M2 screws, M2 heat-set inserts | "30AWG silicone wire", "perfboard", "M2 heat set inserts" | $10 | |
| 12 | Neodymium disc magnets, small (e.g. 6×2 mm) | "6x2mm neodymium magnet" | $3 | Lid sensing and closing the clamshell. |
| 13 | Passive piezo buzzer (small, ~12 mm) | "passive piezo buzzer 3.3V" | $1–2 | Plays the chimes. Driven by PWM on GPIO13 (GPIO12 is the frontlight). Must be **passive**, so it can play different notes. |

**Subtotal now: ~$124–161**

## Order later (power stage 2)

| # | Part | Search terms | ~Cost | Notes |
|---|---|---|---|---|
| 14 | Latching power switch module | "Pololu mini pushbutton power switch" | $6 | Reed switch triggers ON; the Pi triggers OFF via `gpio-poweroff`. Choice not yet verified: confirm it has a separate OFF input. |
| 15 | Reed switch (normally open, glass or SMD) | "reed switch normally open" | $2 | Uses no power, unlike a hall sensor. |
| 16 | USB-C breakout board with 5.1 kΩ CC resistors | "USB-C breakout 5.1k CC" | $3 | VBUS → charger; D+/D− → Pi data port. |
| 17 | *If* the frontlight is a series string: PWM-dimmable LED boost driver board | "LED boost constant current driver PWM dimming" | $3–5 | Only if the datasheet or measurement says ~20 V. |

**Subtotal later: ~$10–15**

## Printing

| Item | ~Cost |
|---|---|
| Test prints at a makerspace/library (filament or fees) | $5–15 |
| Final case from a printing service, coloured parts | $15–30 |

## Total

About **$155–205 + shipping**. The top end goes over the $200 ceiling. The screen kit's real price and shipping decide it. Power stage 2 (~$10–15) can wait until later if money is tight.
