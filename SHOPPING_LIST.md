# Shopping List

Prices are rough estimates in USD, without shipping. Budget ceiling: **~$200 including shipping**.
Links are given only where research found the product page; otherwise use the search terms.
Tools already owned: soldering iron, multimeter, wire strippers, screwdrivers.

## Order now (version 1 + power stage 1)

| # | Part | Search terms / link | ~Cost | Notes |
|---|---|---|---|---|
| 1 | Raspberry Pi Zero 2 W (with pre-soldered header if available — "Zero 2 WH") | "Raspberry Pi Zero 2 WH" from an official reseller | $15–18 | Header saves soldering 40 pins. |
| 2 | microSD card, 32 GB, reputable brand | "SanDisk 32GB microSD A1" | $8 | |
| 3 | 4.2" e-paper with frontlight + touch, **GDEY042T81-FT02** | [buyepaper](https://www.buyepaper.com/products/42-inch-e-paper-display-fast-update-morochrome-spi-e-ink-with-touch-and-front-light-gdey042t81-ft02) · [AliExpress](https://www.aliexpress.us/item/3256805324479823.html) · [Good Display](https://www.good-display.com/product/617.html) | $25–40 (unconfirmed) | **Ask for the datasheet** and whether the frontlight LEDs are series or parallel. Order it first: it's the long-lead item. |
| 4 | Adapter board **DESPI-C02** | Same seller as #3 — "DESPI-C02" | $8 | Connects the panel's 24-pin cable to SPI. |
| 5 | Adafruit **PowerBoost 1000C** | [adafruit.com/product/2465](https://www.adafruit.com/product/2465) | $20 | Charges while running. |
| 6 | Flat LiPo, 3.7 V, 3000–4000 mAh, **with protection circuit and JST-PH connector** | "3.7V 3000mAh LiPo JST PH protected" | $12–18 | Check its size against the battery half (~11 × 15 cm, thin). Match connector polarity to the PowerBoost. |
| 7 | Tactile buttons, 6×6 mm, assorted heights (for D-pad + A/B) | "6x6mm tactile switch assortment" | $3–5 | D-pad = 4 buttons under one printed cap. |
| 8 | Slide switch (SPDT, small) | "mini SPDT slide switch" | $1–2 | Stage 1 power switch; later the hidden hard-off. |
| 9 | Logic-level N-MOSFET (AO3400 or similar) + assorted resistors | "AO3400 SOT-23" or a through-hole "IRLZ44N"; "resistor kit" | $3–5 | For the frontlight **if** the LEDs are parallel. |
| 10 | 5 mm or 3 mm LEDs (blue, red, yellow, green) + resistors | "LED assortment 3mm 5mm" | $3 | Lens + status lights. |
| 11 | Wire, perfboard, female/male headers, M2 screws, M2 heat-set inserts | "30AWG silicone wire", "perfboard", "M2 heat set inserts" | $10 | |
| 12 | Neodymium disc magnets, small (e.g. 6×2 mm) | "6x2mm neodymium magnet" | $3 | Lid sensing and closing the clamshell. |

**Subtotal now: ~$110–140**

## Order later (power stage 2)

| # | Part | Search terms | ~Cost | Notes |
|---|---|---|---|---|
| 13 | Latching power switch module | "Pololu mini pushbutton power switch" | $6 | Reed switch triggers ON; the Pi triggers OFF via `gpio-poweroff`. Choice not yet verified: confirm it has a separate OFF input. |
| 14 | Reed switch (normally open, glass or SMD) | "reed switch normally open" | $2 | Uses no power, unlike a hall sensor. |
| 15 | USB-C breakout board with 5.1 kΩ CC resistors | "USB-C breakout 5.1k CC" | $3 | VBUS → charger; D+/D− → Pi data port. |
| 16 | *If* the frontlight is a series string: PWM-dimmable LED boost driver board | "LED boost constant current driver PWM dimming" | $3–5 | Only if the datasheet or measurement says ~20 V. |

**Subtotal later: ~$10–15**

## Printing

| Item | ~Cost |
|---|---|
| Test prints at a makerspace/library (filament or fees) | $5–15 |
| Final case from a printing service, coloured parts | $15–30 |

## Total

About **$145–185 + shipping**. That leaves a margin under $200 for one broken or wrong part.
