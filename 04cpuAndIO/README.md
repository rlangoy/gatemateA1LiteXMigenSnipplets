# 04 - RiscV SoC with Patched UART (GateMate CC_BRAM FIFO fix)

A full LiteX SoC (RiscV CPU + BIOS) on the Olimex GateMate A1 EVB, with a patched UART core that fixes intermittent echo corruption seen when typing in the LiteX BIOS.

## Overview

This project demonstrates how to:

1. Run a **RiscV SoC** (PicoRV32 or VexRiscV) on the GateMate A1 EVB using LiteX
2. Replace the standard **UART** core with a patched version (`UARTPatched`) using a factory/mixin pattern
3. Override `add_uart()` via **Python MRO** so the patch is applied transparently during `BaseSoC.__init__` — no post-init surgery needed
4. Add a **CSR-mapped LED peripheral** accessible from C firmware running on the CPU
5. Flash a pre-built bitstream without re-running synthesis using `programChipOnly.py`

## Why the UART patch?

The stock LiteX UART core produces intermittent echo corruption (dropped or stale bytes) on the GateMate A1 EVB. The root cause is a FIFO output register mismatch:

- LiteX's `_get_uart_fifo` uses `buffered=True`, which adds an output register stage after the FIFO memory.
- On Xilinx/Intel FPGAs the FIFO memory is LUT-RAM (combinatorial read), so the extra register gives correct 1-cycle latency.
- On GateMate, FIFO depth ≥ 32 is synthesised as **CC_BRAM** (synchronous read, already 1-cycle latency). The extra register stage makes it **2 cycles**, so the CPU reads stale data on every access.

`UARTPatched` fixes this by setting `buffered=False` on the sync FIFO, matching the CC_BRAM single-cycle read latency. It also corrects the TX flush-timer byte-drop race by gating the flush on `source.ready`.

## Architecture

```
 Host PC                          FPGA (GateMate A1)
+-----------------+              +--------------------------------------------+
|                 |   UART       |                                            |
| Terminal        |<------------>| RS232PHY (stock)                           |
|  (115200 baud)  |  TX/RX       |   |                                       |
|                 |              |   | UARTPatched (buffered=False FIFOs)     |
|                 |              |   |                                       |
|                 |              |   v                                       |
|                 |              | RiscV CPU (PicoRV32 / VexRiscV)           |
|                 |              |   | Wishbone / AXI-lite                   |
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
+-----------------+              +--------------------------------------------+
```

## Files

| File | Description |
|---|---|
| `vexriscvLedPeripheral.py` | VexRiscV SoC with patched UART and a CSR-mapped LED peripheral (`LedPeripheral`) controllable from firmware |
| `programChipOnly.py` | Flash a pre-built bitstream to the FPGA SRAM via DirtyJTAG without re-running synthesis |

## Prerequisites

**Yosys version > 0.52 required** — Yosys 0.52 has a bug affecting GateMate builds. Use Yosys 0.63 or newer. See [litex#2426](https://github.com/enjoy-digital/litex/issues/2426) for details.

## Usage

### Build and load (gateMateHardenedTxUart.py)

```bash
# PicoRV32 minimal CPU, build gateware + BIOS, then load into FPGA SRAM
python3 gateMateHardenedTxUart.py --cpu-type picorv32 --cpu-variant minimal --build --load

# Flash to SPI flash (survives power cycle)
python3 gateMateHardenedTxUart.py --cpu-type picorv32 --cpu-variant minimal --build --flash

# Show all available options (Target / Logging / Builder)
python3 gateMateHardenedTxUart.py --help
```

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

### Install the patch directly into LiteX (alternative)

```bash
python3 installUartFix.py
```

Copies `litex_patch/uart.py` over LiteX's installed `soc/cores/uart.py`. This is an alternative to the MRO factory approach — use it if you want all LiteX targets on this machine to pick up the fix without modifying their source.

### Connect a terminal

```bash
litex_term /dev/ttyACM0
   or
picocom -b 115200 /dev/ttyACM0
```

The LiteX BIOS prints to UART at 115200 baud. Adjust the device node to match your USB-UART adapter.

## How It Works

### UART FIFO fix (`uart_tx_fix.py`)

`makeSocUartTxFix(BaseSoC)` dynamically creates a subclass of the given `BaseSoC` class. The subclass overrides `add_uart()`. When `BaseSoC.__init__` calls `self.add_uart(...)`, Python's MRO dispatches to the override, which:

1. Requests the `serial` platform resource via `platform.request(..., loose=True)`
2. Instantiates the stock `RS232PHY` (unchanged)
3. Wraps it in `UARTPatched` (patched FIFOs) instead of the standard `UART`
4. Registers the module with LiteX via `self.add_module()`

Non-serial UART types (crossover, jtag_uart, …) fall through to the parent unchanged.

### Why MRO instead of post-init patching

Attempting to replace the UART after `BaseSoC.__init__` fails in two ways:
- `platform.request("serial")` raises `ConstraintError` because the resource was already consumed
- Re-assigning `self.submodules.uart_phy` appends a second module instead of replacing the first, causing a double-driver error on `pads.tx`

The MRO override sidesteps both problems entirely.

### LedPeripheral (`vexriscvLedPeripheral.py`)

`LedPeripheral` is a one-register Migen `AutoCSR` module. Its single `CSRStorage` bit drives `user_led_n` (active low). LiteX registers it on the CSR bus so the CPU firmware can toggle the LED with a memory-mapped write.

####  vexriscvLedPeripheral - Build Results

| Metric | Value |
|---|---|
| CPE utilisation | ~26% |
| BRAM utilisation | ~44% |
| GPIO utilisation | ~4% |
| Max frequency | 24.83 MHz (constraint: 24 MHz) |
| Programmer | DirtyJTAG via openFPGALoader |
