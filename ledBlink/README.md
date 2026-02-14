# GateMate LED Blink — LiteX / Migen

A minimal LED blinker for the **Cologne Chip GateMate CCGM1A1** FPGA on the **CologneChip GateMate EVB**, built with [LiteX](https://github.com/enjoy-digital/litex) and [Migen](https://github.com/m-labs/migen).

## What it does

A 26-bit counter increments on every rising edge of the 10 MHz board clock (`clk10`). Bit 23 drives `user_led_n0`, toggling the LED roughly every ~1.2 seconds.

## Prerequisites

- Python 3 with **LiteX** and **Migen** installed
- **Yosys** (synthesis)
- **Cologne Chip p_r** place-and-route toolchain
- **openFPGALoader** (programming)
- A JTAG adapter (e.g. DirtyJTAG)

## Build

```bash
python3 blinkLed.py
```

This generates the bitstream and all build artifacts under `build/`.

## Ceck Programmer:
```bash
Run:
   openFPGALoader --detect --cable dirtyJtag
Should return:
  empty
  Jtag frequency : requested 6000000Hz -> real 6000000Hz
  index 0:
        idcode 0x20000001
        manufacturer colognechip
        family GateMate Series
        model  GM1Ax
        irlength 6
```


## Program the FPGA

```bash
openFPGALoader --cable dirtyJtag build/top_00.cfg
```

> **Note:** Use the `.cfg` file, not `.cfg.bit`. The `.cfg.bit` wrapper is not recognized by openFPGALoader for GateMate targets.

## Project structure

```
blinkLed.py          # LiteX/Migen design — 26-bit counter driving an LED
build/
  top.v              # Generated Verilog
  top.ccf            # Constraint file (pin assignments)
  build_top.sh       # Yosys + p_r build script
  top_00.cfg         # Bitstream for FPGA programming
```
