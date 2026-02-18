# 02 - Wishbone LED Control via UART Bridge

Control an LED on the Olimex GateMate A1 EVB from a host PC over UART, using a Wishbone bus.

## Overview

This project demonstrates how to:

1. Create a **Wishbone slave peripheral** (a 1-bit LED register) using Migen
2. Use LiteX's **UARTWishboneBridge** to expose the Wishbone bus to the host PC
3. Control the peripheral from a **host-side Python script** using `RemoteClient`

Two direct-mapping variants exist, differing only in their LED address:

| File | LED byte address | LED word address |
|---|---|---|
| `uartWishBoneDirectMapingLed.py` | `0x40000400` | `0x10000100` |

## Architecture

### `uartWishBoneDirectMapingLed.py`

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
|                 |             |     - Only writes reg at mapped    |
|                 |             |       address update LED           |
|                 |             |     - bit 0 -> LED                 |
+-----------------+             +------------------------------------+
```

### `uartWishBoneCrsLed.py`

```
 Host PC                         FPGA (GateMate A1)
+-----------------+             +------------------------------------+
|                 |   UART      |                                    |
| litex_server    |<----------->| UARTWishboneBridge                 |
|   (115200 baud) |  TX/RX      |   (Wishbone master)               |
|                 |             |        |                           |
| RemoteClient    |             |        | Wishbone bus              |
|   wb.write()    |             |        v                           |
|   wb.read()     |             |   CSR Decoder (SoCMini)            |
|                 |             |        |                           |
|                 |             |        v                           |
|                 |             |   LedPeripheral (CSR slave)        |
|                 |             |     - control register @ 0x40000400|
|                 |             |     - bit 0 -> LED                 |
+-----------------+             +------------------------------------+
```

## Files

| File | Description |
|---|---|
| `uartWishBoneDirectMapingLed.py` | FPGA design: UART bridge + direct Wishbone LED peripheral at `0x40000400` |
| `uartWishBoneCrsLed.py` | FPGA design: UART bridge + LiteX SoCMini/CSR-based LED peripheral |
| `wishBoneUartDebugLedPeripheralModule.py` | Host-side interactive script to toggle the LED at `0x40000400` via RemoteClient |
| `testBenchLedPeripheral.py` | Simulation testbench verifying address decoding for `uartWishBoneCrsLed.py` (address `0x40000400`) |
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

**Option A** — `wishBoneBlink.py` (LED at `0x40000000`, outputs `build/top_00.cfg`):

```bash
python wishBoneBlink.py
```

**Option B** — `uartWishBoneDirectMapingLed.py` (LED at `0x40000400`, outputs `build/gateware/olimex_gatemate_a1_evb_00.cfg`):

```bash
python uartWishBoneDirectMapingLed.py
```

### 2. Load the bitstream onto the FPGA

For Option A:

```bash
openFPGALoader -c dirtyJtag build/top_00.cfg
```

For Option B:

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
python wishBoneUartDebugLedPeripheralModule.py
```

This is an interactive loop. It writes to `0x40000400`, reads back the register, and waits for Enter between steps. It also tests that writing to an unmapped address (`0x40000004`) has no effect:

```
 Write 0x01 to address 0x40000400  — turns the LED on - please verify
LED register = 0x00000001 (bit0=ON)
Press Enter to continue...
Turn led off -- please verify
LED register = 0x00000000 (bit0=OFF)
Press Enter to continue...
 Write 0x01 to address 0x40000004  — No device attached nothing should happen - please verify
...
```

### Manual control via Python REPL

```python
from litex import RemoteClient

wb = RemoteClient()
wb.open()

wb.write(0x40000400, 0x1)   # LED on  (use 0x40000000 if running wishBoneBlink.py)
wb.write(0x40000400, 0x0)   # LED off

value = wb.read(0x40000400)  # Read back register
print(f"LED = {'ON' if value & 1 else 'OFF'}")

wb.close()
```

## Register Map

### `wishBoneBlink.py`

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000000` | 0 | R/W | LED control (1 = on, 0 = off) |

### `uartWishBoneDirectMapingLed.py`

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000400` | 0 | R/W | LED control (1 = on, 0 = off) |

### `uartWishBoneCrsLed.py` (CSR-based)

| Address | Bit | R/W | Description |
|---|---|---|---|
| `0x40000400` | 0 | R/W | LED control via `led.control` CSR register |

## How It Works

- **UARTWishboneBridge** (`litex.soc.cores.uart`) instantiates an RS232 PHY and a protocol converter (`Stream2Wishbone`) that translates serial commands from `litex_server` into Wishbone bus transactions.
- **WishboneLed** is a Wishbone slave with built-in address decoding. It **always ACKs every transaction** to prevent the `Stream2Wishbone` state machine from hanging on unmapped addresses (see [litex#82](https://github.com/enjoy-digital/litex/issues/82)). Only writes to the mapped address update the LED register. Reads from other addresses return 0.
- The slave drives the active-low LED pin accordingly (`led_n = ~reg`).
- The bridge and slave are connected directly (no external Decoder needed).

## Running Tests

```bash
python testBenchLedPeripheral.py
```

This runs a Migen simulation for the `uartWishBoneCrsLed.py` design (LED at `0x40000400`) and verifies:

- Writes to `0x40000400` update the LED register
- Writes to other addresses (`0x50000000`, `0x20000000`, `0x00000000`, `0x40000404`) are ACKed but do not affect the LED
- The bus never hangs on any address
- Read-back returns the correct value

A `test_address_decode.vcd` waveform file is generated for inspection in GTKWave.
