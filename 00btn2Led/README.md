# 00 - Button to LED (Combinatorial Logic)

Simple example showing how to use LiteX/Migen with only combinatorial logic on the Olimex GateMate A1 EVB.

## Overview

This project demonstrates how to:

1. Define a minimal **platform** for the GateMate A1 EVB using `CologneChipPlatform`
2. Create a **Migen module** with pure combinatorial logic (`comb`)
3. Wire a button directly to an LED — no clock, no state

## Architecture

```
 Button                          FPGA (GateMate A1)
+-----------------+             +------------------------------------+
|                 |             |                                    |
| user_btn_n      |------------>| Btn2Led                            |
| (IO_SB_B7)      |   comb      |   led.eq(btn)                      |
|                 |             |        |                           |
|                 |             |        v                           |
|                 |             |   user_led_n                       |
|                 |             |   (IO_SB_B6)                       |
+-----------------+             +------------------------------------+
```

## Files

| File | Description |
|---|---|
| `btn2Led.py` | FPGA design: minimal platform + combinatorial button-to-LED module |

## Hardware Requirements

- **Board**: Olimex GateMate A1 EVB (CCGM1A1 FPGA)
- **Clock**: 10 MHz on-board oscillator (`IO_SB_A8`) — declared but unused (combinatorial only)
- **LED**: `user_led_n` on `IO_SB_B6` (active low)
- **Button**: `user_btn_n` on `IO_SB_B7` (active low)

## Dependencies

- [Migen](https://github.com/m-labs/migen)
- [LiteX](https://github.com/enjoy-digital/litex) (provides `CologneChipPlatform`)
- [Yosys](https://github.com/YosysHQ/yosys) + [openFPGALoader](https://github.com/trabucayre/openFPGALoader) (synthesis and programming)

## Usage

### 1. Build and program the bitstream

```bash
python btn2Led.py
```

This builds the bitstream to `build/top_00.cfg` and immediately programs the FPGA via `openFPGALoader`.

### 2. Manual programming (if needed)

```bash
openFPGALoader -c dirtyJtag build/top_00.cfg
```

## How It Works

- **`Btn2Led`** is a Migen `Module` containing a single combinatorial assignment: `led.eq(btn)`.
- Since both signals are active-low, pressing the button pulls `user_btn_n` low, which drives `user_led_n` low, turning the LED on.
- There is no clock domain, no synchronous logic, and no state — the LED mirrors the button instantly.
- The platform is defined inline (normally it would be imported from `litex_boards.platforms.olimex_gatemate_a1_evb`).
