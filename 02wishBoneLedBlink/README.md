# 02wishBoneLedBlink - CSR LED Control via UART Wishbone Bridge

Control an LED on the **Olimex GateMate A1 EVB** from a host PC over UART, using a LiteX SoCMini with a CSR-mapped LED peripheral.

## Overview

This project demonstrates how to:

1. Build a minimal **LiteX SoCMini** (no CPU) with a UART Wishbone bridge as the bus master
2. Create a **CSR-mapped LED peripheral** (`LedPeripheral`) using Migen and `AutoCSR`
3. Control the LED from the host PC using `litex_server` and `RemoteClient`

## Architecture

```
 Host PC                          FPGA (GateMate A1)
+-----------------+              +--------------------------------------------+
|                 |   UART       |                                            |
| litex_server    |<------------>| UARTWishboneBridge                         |
|   (115200 baud) |  TX/RX       |   (Wishbone master)                       |
|                 |              |        |                                   |
| RemoteClient    |              |        | Wishbone bus                      |
|   wb.write()    |              |        v                                   |
|   wb.read()     |              |   CSR Decoder (SoCMini)                   |
|                 |              |        |                                   |
|                 |              |        v                                   |
|                 |              |   LedPeripheral (CSR slave)                |
|                 |              |     - control @ 0x40000400                 |
|                 |              |       bit 0: 1 = LED on, 0 = LED off       |
+-----------------+              +--------------------------------------------+
```

## Files

| File | Description |
|---|---|
| `socMiniUartWishBoneCrsLed.py` | FPGA design: SoCMini + UARTWishboneBridge + CSR-mapped LED peripheral. Builds and loads the bitstream when run directly. |

## Hardware Requirements

- **Board**: Olimex GateMate A1 EVB (CCGM1A1 FPGA)
- **USB-UART adapter** connected to the board's serial pins:
  - TX: `IO_SA_B6`
  - RX: `IO_SA_A6`
- **Clock**: 10 MHz on-board oscillator (`IO_SB_A8`)
- **LED**: `user_led_n` on `IO_SB_B6` (active low)

## Dependencies

- [Migen](https://github.com/m-labs/migen)
- [LiteX](https://github.com/enjoy-digital/litex) (provides `UARTWishboneBridge`, `RemoteClient`, `litex_server`)
- [LiteX-Boards](https://github.com/litex-hub/litex-boards) (provides the Olimex GateMate A1 EVB platform)
- [Yosys](https://github.com/YosysHQ/yosys) + [openFPGALoader](https://github.com/trabucayre/openFPGALoader) (synthesis and programming)

## Usage

### 1. Build and load the bitstream

```bash
python3 socMiniUartWishBoneCrsLed.py
```

This builds the gateware under `build/` and immediately loads the bitstream into the FPGA SRAM via DirtyJTAG.

### 2. Start the LiteX UART server

```bash
litex_server --uart --uart-port=/dev/ttyACM0
```

Adjust `/dev/ttyACM0` to match your USB-UART adapter.

### 3. Control the LED

```python
from litex.tools.remote import RemoteClient

wb = RemoteClient()
wb.open()

wb.regs.led_control.write(1)   # LED on
wb.regs.led_control.write(0)   # LED off

wb.close()
```

Or using raw Wishbone addresses:

```python
wb.write(0x40000400, 0x1)   # LED on
wb.write(0x40000400, 0x0)   # LED off
value = wb.read(0x40000400) # Read back
```

## Register Map

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000400` | 0 | R/W | LED control (`led_control`): 1 = on, 0 = off |

Full CSR map is generated at `build/csr.csv` after building.

## How It Works

- **SoCMini** is initialised with `uart_name="crossover"` to suppress the default UART peripheral. The physical serial pads are instead claimed by `UARTWishboneBridge` directly.
- **UARTWishboneBridge** translates commands from `litex_server` into Wishbone bus transactions, making the host PC the bus master.
- **LedPeripheral** is a one-register `AutoCSR` module. Its single `CSRStorage` bit drives `user_led_n` (active low: `reg=1` pulls the pin low, turning the LED on).
- LiteX's CSR decoder maps the register to `0x40000400` using `csr_base=0x40000000` and `csr_paging=0x400` (slot 1 × 0x400 = offset 0x400).
