# 04 - RiscV SoC and Memory Mapped I/O

A full LiteX SoC (RiscV CPU + BIOS) on the Olimex GateMate A1 EVB, with a custom CSR (memory mapped I/O) interface

## Overview

This project demonstrates how to:

1. Run a **RiscV SoC**  VexRiscV on the GateMate A1 EVB using LiteX
4. Add a **CSR-mapped LED peripheral** accessible from C firmware running on the CPU
5. Flash a pre-built bitstream without re-running synthesis using `programChipOnly.py`

## Architecture

```
 Host PC                          FPGA (GateMate A1)
+-----------------+              +-------------------------------------------+
|                 |   UART       |                                           |
| Terminal        |<------------>| RS232PHY (stock)                          |
|  (115200 baud)  |  TX/RX       |   |                                       |
|                 |              |   |                                       |
|                 |              |   v                                       |
|                 |              | RiscV CPU (VexRiscV)                      |
|                 |              |   | Wishbone                              |
|                 |              |   v                                       |
|                 |              | LiteX BIOS  (runs from BRAM)              |
|                 |              |   |                                       |
|                 |              |   v                                       |
|                 |              | CSR bus                                   |
|                 |              |   |                                       |
|                 |              |   v                                       |
|                 |              | LedPeripheral  (vexriscvLedPeripheral.py) |
|                 |              |   - control @ CSR offset 0                |
|                 |              |   - bit 0 → user_led_n                    |
+-----------------+              +-------------------------------------------+
```

## Files

| File | Description |
|---|---|
| `vexriscvLedPeripheral.py` | VexRiscV SoC with a CSR-mapped LED peripheral (`LedPeripheral`) controllable from firmware |
| `programChipOnly.py` | Flash a pre-built bitstream to the FPGA SRAM via DirtyJTAG without re-running synthesis |

## Prerequisites

**Yosys version > 0.52 required** — Yosys 0.52 has a synthesis bug that corrupts the UART TX path when FIFO depth exceeds 4, causing BIOS echo corruption. Use Yosys 0.63 or newer. See [litex#2426](https://github.com/enjoy-digital/litex/issues/2426) for details.

## Known Issue: BIOS UART Echo Corruption

With Yosys 0.52 (e.g. Ubuntu 25.10 apt package), the BIOS console echoes garbled characters — typing "help" may display as "h%lp". The receive path works correctly (Enter still executes the right command), but the TX path is corrupted by a Yosys synthesis bug affecting UART FIFOs with depth > 4.

**Fix:** Upgrade to Yosys 0.63+ (build from source or use OSS CAD Suite). No code changes needed.

**Workaround:** Pass `--uart-fifo-depth 4` to avoid the buggy synthesis path.

## Usage

### Build and load (vexriscvLedPeripheral.py)

```bash
python3 vexriscvLedPeripheral.py
```

This builds with VexRiscV, adds the `LedPeripheral` CSR, and immediately loads the bitstream into FPGA SRAM via DirtyJTAG.

### Flash a pre-built bitstream only

```bash
python3 programChipOnly.py
```

Streams the bitstream at `build/gateware/olimex_gatemate_a1_evb_00.cfg.bit` into the FPGA SRAM without re-running synthesis.

### Connect a terminal

```bash
litex_term /dev/ttyACM0
   or
picocom -b 115200 /dev/ttyACM0
```

The LiteX BIOS prints to UART at 115200 baud. Adjust the device node to match your USB-UART adapter.

## How It Works


### LedPeripheral (`vexriscvLedPeripheral.py`)

`LedPeripheral` is a one-register Migen `AutoCSR` module. Its single `CSRStorage` bit drives `user_led_n` (active low). LiteX registers it on the CSR bus so the CPU firmware can toggle the LED with a memory-mapped write.

####  vexriscvLedPeripheral - Build Results

Built with Yosys 0.63, VexRiscV minimal variant, 24 MHz system clock.

| Metric | Value |
|---|---|
| CPE utilisation | ~17% |
| BRAM utilisation | ~31% |
| GPIO utilisation | ~4% |
| Max frequency | 27.96 MHz (constraint: 24 MHz) |
| Programmer | DirtyJTAG via openFPGALoader |
