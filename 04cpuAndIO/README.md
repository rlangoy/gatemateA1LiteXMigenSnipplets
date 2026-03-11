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
| `picorvLedAndCrc32Peripherial.py` | PicoRV32 SoC with both a CSR-mapped LED peripheral and a CRC32 peripheral (VHDL black-box via GHDL plugin) |
| `programChipOnly.py` | Flash a pre-built bitstream to the FPGA SRAM via DirtyJTAG without re-running synthesis |
| `mycsrlib/` | Reusable CSR peripheral library containing `CRC32Peripheral` and `GhdlCologneChipToolchain` — see [`mycsrlib/INSTALL.md`](mycsrlib/INSTALL.md) for GHDL plugin setup |

## Prerequisites

- **Yosys version > 0.52 required** — Yosys 0.52 has a synthesis bug that corrupts the UART TX path when FIFO depth exceeds 4, causing BIOS echo corruption. Use Yosys 0.63 or newer. See [litex#2426](https://github.com/enjoy-digital/litex/issues/2426) for details.
- **GHDL Yosys plugin** (for `picorvLedAndCrc32Peripherial.py` only) — required to synthesise the VHDL CRC32 entity. See [`mycsrlib/INSTALL.md`](mycsrlib/INSTALL.md) for build instructions.

## Known Issue: BIOS UART Echo Corruption

With Yosys 0.52 (e.g. Ubuntu 25.10 apt package), the BIOS console echoes garbled characters — typing "help" may display as "h%lp". The receive path works correctly (Enter still executes the right command), but the TX path is corrupted by a Yosys synthesis bug affecting UART FIFOs with depth > 4.

**Fix:** Upgrade to Yosys 0.63+  (No code changes needed.)

## Usage

### Build and load (vexriscvLedPeripheral.py)

```bash
python3 vexriscvLedPeripheral.py
```

This builds with VexRiscV, adds the `LedPeripheral` CSR, and immediately loads the bitstream into FPGA SRAM via DirtyJTAG.

### Build and load (picorvLedAndCrc32Peripherial.py)

```bash
python3 picorvLedAndCrc32Peripherial.py
```

This builds a PicoRV32 SoC with both the `LedPeripheral` CSR and a `CRC32Peripheral` (VHDL black-box), and immediately loads the bitstream into FPGA SRAM via DirtyJTAG. Requires the GHDL Yosys plugin — see [`mycsrlib/INSTALL.md`](mycsrlib/INSTALL.md).

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

### PicoRV32 SoC with LED + CRC32 (`picorvLedAndCrc32Peripherial.py`)

`picorvLedAndCrc32Peripherial.py` builds a PicoRV32-based SoC (minimal variant, 24 MHz) with two CSR peripherals:

- **LedPeripheral** — same one-register `AutoCSR` module as above, driving `user_led_n`.
- **CRC32Peripheral** — a CRC-32/ISO-HDLC accumulator backed by a VHDL entity (`mycsrlib/hdl/crc.vhdl`). Exposes two CSR registers: `data` (write a byte / read the running checksum) and `reset_ctrl` (write any value to reset the accumulator). Uses `GhdlCologneChipToolchain` to patch the Yosys script for GHDL plugin support at build time.

####  vexriscvLedPeripheral - Build Results

Built with Yosys 0.63, VexRiscV minimal variant, 24 MHz system clock.

| Metric | Value |
|---|---|
| CPE utilisation | ~17% |
| BRAM utilisation | ~31% |
| GPIO utilisation | ~4% |
| Max frequency | 27.96 MHz (constraint: 24 MHz) |
| Programmer | DirtyJTAG via openFPGALoader |
