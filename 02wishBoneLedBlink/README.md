# 02 - Wishbone LED Control via UART Bridge

Control an LED on the Olimex GateMate A1 EVB from a host PC over UART, using a Wishbone bus.

## Overview

This project demonstrates how to:

1. Create a **Wishbone slave peripheral** (a 1-bit LED register) using Migen
2. Use LiteX's **UARTWishboneBridge** to expose the Wishbone bus to the host PC
3. Control the peripheral from a **host-side Python script** using `RemoteClient`

The LED is mapped to **bit 0** at address **0x40000000**. Writing `0x1` turns the LED on, writing `0x0` turns it off.

## Architecture

```
 Host PC                         FPGA (GateMate A1)
+-----------------+             +------------------------------------+
|                 |   UART      |                                    |
| litex_server    |<----------->| UARTWishboneBridge                 |
|   (115200 baud) |  TX/RX      |   (Wishbone master)               |
|                 |             |        |                           |
| RemoteClient    |             |        | Wishbone bus              |
|   wb.write()    |             |        v                           |
|   wb.read()     |             |   WishboneLed (slave)              |
|                 |             |     bit 0 -> LED                   |
+-----------------+             +------------------------------------+
```

## Files

| File | Description |
|---|---|
| `wishBoneBlink.py` | FPGA design: UART bridge + Wishbone LED peripheral |
| `ledControl.py` | Host-side script to turn the LED on and read back the register |
| `designspec.md` | Original design specification |

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

### 1. Build the bitstream

```bash
python wishBoneBlink.py
```

This runs Yosys synthesis and Cologne Chip place-and-route, producing `build/top_00.cfg`.

### 2. Load the bitstream onto the FPGA

```bash
openFPGALoader -c dirtyJtag build/top_00.cfg
```

### 3. Start the LiteX UART server

```bash
litex_server --uart --uart-port=/dev/ttyUSB0
```

Adjust `/dev/ttyUSB0` to match your USB-UART adapter.

### 4. Control the LED

```bash
python ledControl.py
```

Expected output:

```
LED register = 0x00000001 (bit0=ON)
```

### Manual control via Python REPL

```python
from litex import RemoteClient

wb = RemoteClient()
wb.open()

wb.write(0x40000000, 0x1)   # LED on
wb.write(0x40000000, 0x0)   # LED off

value = wb.read(0x40000000)  # Read back register
print(f"LED = {'ON' if value & 1 else 'OFF'}")

wb.close()
```

## Register Map

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000000` | 0 | R/W | LED control (1 = on, 0 = off) |

## How It Works

- **UARTWishboneBridge** (`litex.soc.cores.uart`) instantiates an RS232 PHY and a protocol converter (`Stream2Wishbone`) that translates serial commands from `litex_server` into Wishbone bus transactions.
- **WishboneLed** is a minimal Wishbone slave that latches bit 0 on write and drives the active-low LED pin accordingly (`led_n = ~reg`).
- The two are connected point-to-point on the Wishbone bus (no address decoder needed for a single slave).
