# Design Specification: Wishbone LED Control via UART Bridge

## 1. Objective

Demonstrate how to create a Wishbone bus peripheral that controls an LED, accessible from a host PC over a UART bridge. The LED is mapped to **bit 0** of a register at address **0x40000000**.

## 2. Target Hardware

| Parameter | Value |
|---|---|
| Board | Olimex GateMate A1 EVB |
| FPGA | Cologne Chip CCGM1A1 |
| Clock | 10 MHz on-board oscillator (`IO_SB_A8`) |
| LED | `user_led_n` on `IO_SB_B6` (active low) |
| UART TX | `IO_SA_B6` |
| UART RX | `IO_SA_A6` |
| UART baudrate | 115200 |

## 3. Functional Requirements

### 3.1 FPGA Design (`wishBoneBlink.py`)

- **FR-1**: A Wishbone slave peripheral (`WishboneLed`) shall provide a 1-bit read/write register controlling the LED.
  - Writing `0x1` to bit 0 turns the LED **on** (active-low: `led_n = ~reg`).
  - Writing `0x0` to bit 0 turns the LED **off**.
  - Reading returns the current register value.

- **FR-2**: A `UARTWishboneBridge` (from `litex.soc.cores.uart`) shall act as the Wishbone bus master, translating UART serial commands from the host into Wishbone transactions.

- **FR-3**: The bridge master and LED slave shall be connected point-to-point on the Wishbone bus.

- **FR-4**: The LED signal shall be obtained via `platform.request("user_led_n", 0)`.

- **FR-5**: The UART pads shall be obtained via `platform.request("serial")`.

### 3.2 Host-Side Control (`ledControl.py`)

- **FR-6**: A host-side Python script shall use `RemoteClient` from LiteX to communicate with the FPGA over the UART bridge.

- **FR-7**: The script shall write `0x1` to address `0x40000000` to turn the LED on, then read back the value to verify.

### 3.3 LiteX Server

- **FR-8**: The LiteX server shall be started in UART mode before running the host-side script:
  ```
  litex_server --uart --uart-port=/dev/ttyUSBX
  ```

## 4. Register Map

| Address | Bit(s) | Name | Access | Reset | Description |
|---|---|---|---|---|---|
| `0x40000000` | 0 | `led_reg` | R/W | 0 | LED control: 1 = on, 0 = off |
| `0x40000000` | 31:1 | - | R | 0 | Reserved (reads as 0) |

## 5. Wishbone Bus Interface

| Signal | Direction (slave) | Description |
|---|---|---|
| `cyc` | Input | Bus cycle active |
| `stb` | Input | Strobe / valid transfer |
| `we` | Input | Write enable |
| `ack` | Output | Transfer acknowledge (1-cycle latency) |
| `dat_w[31:0]` | Input | Write data (only bit 0 used) |
| `dat_r[31:0]` | Output | Read data (bit 0 = `led_reg`) |

## 6. Design Decisions

- **Point-to-point bus**: No address decoder is needed since there is only one slave. The slave responds to all addresses.
- **Active-low LED**: The board's LED is active low (`user_led_n`), so the output is inverted: `led_n = ~led_reg`.
- **No full SoC**: This is a raw Migen design using only `UARTWishboneBridge` from LiteX, not a full LiteX SoC. This keeps the design minimal and focused on the Wishbone bus concept.

## 7. Dependencies

| Package | Purpose |
|---|---|
| [Migen](https://github.com/m-labs/migen) | HDL generation framework |
| [LiteX](https://github.com/enjoy-digital/litex) | `UARTWishboneBridge`, `RemoteClient`, `litex_server` |
| [LiteX-Boards](https://github.com/litex-hub/litex-boards) | Olimex GateMate A1 EVB platform definition |
| [Yosys](https://github.com/YosysHQ/yosys) | Verilog synthesis |
| [p_r (Cologne Chip)](https://colognechip.com/) | Place and route for GateMate |
| [openFPGALoader](https://github.com/trabucayre/openFPGALoader) | Bitstream programming |

## 8. Build and Test Procedure

```
# Step 1: Build bitstream
python wishBoneBlink.py

# Step 2: Load bitstream
openFPGALoader -c dirtyJtag build/top_00.cfg

# Step 3: Start UART server
litex_server --uart --uart-port=/dev/ttyUSB0

# Step 4: Control LED from host
python ledControl.py
```

### Expected Output

```
LED register = 0x00000001 (bit0=ON)
```

## 9. References

- [LiteX Wiki: Use Host Bridge to control/debug a SoC](https://github.com/enjoy-digital/litex/wiki/Use-Host-Bridge-to-control-debug-a-SoC)
- [LiteX Wiki](https://github.com/enjoy-digital/litex/wiki)
