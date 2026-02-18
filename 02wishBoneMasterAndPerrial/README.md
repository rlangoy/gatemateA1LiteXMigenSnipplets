# 02 - Wishbone LED Control via UART Bridge

Control an LED on the Olimex GateMate A1 EVB from a host PC over UART, using a Wishbone bus.

## Overview

This project demonstrates how to:

1. Create a **Wishbone slave peripheral** (a 1-bit LED register) using Migen
2. Use LiteX's **UARTWishboneBridge** to expose the Wishbone bus to the host PC
3. Control the peripheral from a **host-side Python script** using `RemoteClient`

The LED is mapped to **bit 0** at address **0x40000400**. Writing `0x1` turns the LED on, writing `0x0` turns it off.

## Architecture

```
 Host PC                         FPGA (GateMate A1)
+-----------------+             +------------------------------------+
|                 |   UART      |                                    |
| litex_server    |<----------->| UARTWishboneBridge                 |
|   (115200 baud) |  TX/RX      |   (Wishbone master)               |
|                 |             |        |                           |
| RemoteClient    |             |        | Wishbone bus (direct)     |
|   wb.write()    |             |        v                           |
|   wb.read()     |             |   WishboneLed (slave)              |
|                 |             |     - Always ACKs every address    |
|                 |             |     - Only writes reg at 0x4000..  |
|                 |             |     - bit 0 -> LED                 |
+-----------------+             +------------------------------------+
```

## Files

| File | Description |
|---|---|
| `uartWishBoneDirectMapingLed.py` | FPGA design: UART bridge + direct Wishbone address-decoded LED peripheral |
| `uartWishBoneCrsLed.py` | FPGA design: UART bridge + LiteX SoCMini/CSR-based LED peripheral |
| `wbTestLedModule.py` | Host-side script to toggle the LED via RemoteClient |
| `test_address_decode.py` | Simulation testbench verifying address decoding |
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
python uartWishBoneDirectMapingLed.py
```

This runs Yosys synthesis and Cologne Chip place-and-route, producing `build/gateware/olimex_gatemate_a1_evb_00.cfg`.

### 2. Load the bitstream onto the FPGA

```bash
openFPGALoader -c dirtyJtag build/gateware/olimex_gatemate_a1_evb_00.cfg
```

### 3. Start the LiteX UART server

```bash
litex_server --uart --uart-port=/dev/ttyACM0 --debug
```

Adjust `/dev/ttyACM0` to match your USB-UART adapter.

### 4. Control the LED

```bash
python wbTestLedModule.py
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

wb.write(0x40000400, 0x1)   # LED on
wb.write(0x40000400, 0x0)   # LED off

value = wb.read(0x40000400)  # Read back register
print(f"LED = {'ON' if value & 1 else 'OFF'}")

wb.close()
```

## Register Map

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000400` | 0 | R/W | LED control (1 = on, 0 = off) |

## How It Works

- **UARTWishboneBridge** (`litex.soc.cores.uart`) instantiates an RS232 PHY and a protocol converter (`Stream2Wishbone`) that translates serial commands from `litex_server` into Wishbone bus transactions.
- **WishboneLed** is a Wishbone slave with built-in address decoding. It **always ACKs every transaction** to prevent the `Stream2Wishbone` state machine from hanging on unmapped addresses (see [litex#82](https://github.com/enjoy-digital/litex/issues/82)). Only writes to address `0x40000400` (word address `0x10000100`) update the LED register. Reads from other addresses return 0.
- The slave drives the active-low LED pin accordingly (`led_n = ~reg`).
- The bridge and slave are connected directly (no external Decoder needed).

## Running Tests

```bash
python test_address_decode.py
```

This runs a Migen simulation that verifies:
- Writes to `0x40000000` update the LED register
- The bus never hangs on unmapped addresses
- Read-back returns the correct value
