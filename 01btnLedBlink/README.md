# GateMate blink led when user button is pushed  LiteX / Migen

A minimal LED blinker for the **Cologne Chip GateMate CCGM1A1** FPGA on the **CologneChip GateMate EVB**, built with [LiteX](https://github.com/enjoy-digital/litex) and [Migen](https://github.com/m-labs/migen).

## What it does

if the user button is pushed the `user_led_n0` is toggling every ~1.2 seconds.

## Prerequisites

- Python 3 with **LiteX** and **Migen** installed

## Build and flash the program

```bash
python3 btnLedBlink.py
```

This generates the bitstream (top_00.cfg) and all build artifacts under `build/`.


## Project structure

```
btnLedBlink.py          # LiteX/Migen design — 26-bit counter driving an LED
build/
  top.v              # Generated Verilog
  top.ccf            # Constraint file (pin assignments)
  build_top.sh       # Yosys + p_r build script
  top_00.cfg         # Bitstream for FPGA programming
```
