# 01 - LED Blink

Blink an LED on the **Olimex GateMate A1 EVB** from a free-running counter, built with [LiteX](https://github.com/enjoy-digital/litex) and [Migen](https://github.com/m-labs/migen).

## Overview

This project demonstrates how to:

1. Create a simple **Migen Module** with a free-running 26-bit counter
2. Drive an LED from a counter bit to produce a visible blink rate
3. Build and program a bitstream using the **LiteX platform build flow**

## Architecture

```
 FPGA (GateMate A1)
+-----------------------------+
|   Blink (Module)            |
|     - 26-bit free counter   |
|     - bit 23 → user_led_n   |
|       (~0.84 s half-period) |
+-----------------------------+
```

## Files

| File | Description |
|---|---|
| `blinkLed.py` | FPGA design: 26-bit counter driving `user_led_n` via bit 23 |

## Hardware Requirements

- **Board**: Olimex GateMate A1 EVB (CCGM1A1 FPGA)
- **Clock**: 10 MHz on-board oscillator (`IO_SB_A8`)
- **LED**: `user_led_n` on `IO_SB_B6` (active low)

## Dependencies

- [Migen](https://github.com/m-labs/migen)
- [LiteX](https://github.com/enjoy-digital/litex)
- [LiteX-Boards](https://github.com/litex-hub/litex-boards) (provides the Olimex GateMate A1 EVB platform)
- [Yosys](https://github.com/YosysHQ/yosys) + [openFPGALoader](https://github.com/trabucayre/openFPGALoader) (synthesis and programming)

## Usage

### 1. Build the bitstream

```bash
python blinkLed.py
```

This generates the bitstream and all build artifacts under `build/`.

### 2. Check programmer

```bash
openFPGALoader --detect --cable dirtyJtag
```

Should return:

```
empty
Jtag frequency : requested 6000000Hz -> real 6000000Hz
index 0:
      idcode 0x20000001
      manufacturer colognechip
      family GateMate Series
      model  GM1Ax
      irlength 6
```

### 3. Load the bitstream onto the FPGA

```bash
openFPGALoader -c dirtyJtag build/top_00.cfg
```

> **Note:** Use the `.cfg` file, not `.cfg.bit`. The `.cfg.bit` wrapper is not recognized by openFPGALoader for GateMate targets.

## How It Works

A 26-bit counter increments on every rising edge of the 10 MHz board clock. Bit 23 is wired combinatorially to `user_led_n`, toggling the LED at roughly 0.6 Hz (2^23 ÷ 10 MHz ≈ 0.84 s half-period).

The LED pin is active-low, so `counter[23] = 1` drives the pin low and turns the LED on.
