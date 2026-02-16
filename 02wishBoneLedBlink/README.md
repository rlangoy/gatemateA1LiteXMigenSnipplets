# 02 Wishbone LED Blink

A Migen/LiteX example demonstrating a Wishbone bus peripheral on the **Olimex GateMate A1-EVB** FPGA board. A button press triggers a Wishbone bus transaction that enables LED blinking.

## How It Works

The design consists of three modules connected via a Wishbone bus:

### WishboneBlink (Slave)
- Exposes a single-bit register (`enableBlinking`) as a Wishbone slave
- Writing `1` to bit 0 enables LED blinking using a 26-bit counter (visible on bit 23)
- Writing `0` turns the LED off (active-low LED, so `led_n=1` = off)
- Reading returns the current `enableBlinking` state

### WishboneMaster (Master)
- Monitors the user button for press/release edges
- On button press (falling edge): issues a Wishbone write with `dat_w=1` (enable blinking)
- On button release (rising edge): issues a Wishbone write with `dat_w=0` (disable blinking)
- Uses a simple FSM: `IDLE` -> `WRITE_ON`/`WRITE_OFF` -> `IDLE`

### Top
- Connects master and slave via `master.bus.connect(blink.bus)`
- Requests `user_led_n` and `user_btn_n` I/O from the platform

## Wishbone Bus Signals Used

| Signal   | Direction (Master) | Description                        |
|----------|--------------------|------------------------------------|
| `cyc`    | Output             | Bus cycle active                   |
| `stb`    | Output             | Strobe - valid transfer            |
| `we`     | Output             | Write enable                       |
| `ack`    | Input              | Slave acknowledges transfer        |
| `dat_w`  | Output             | Write data (bit 0 = enableBlinking)|
| `dat_r`  | Input              | Read data                          |

## Requirements

- Python 3
- [Migen](https://github.com/m-labs/migen)
- [LiteX](https://github.com/enjoy-digital/litex) (with `litex_boards`)
- [Yosys](https://github.com/YosysHQ/yosys) (synthesis)
- [GateMate p_r](https://colognechip.com/) (place & route)
- [openFPGALoader](https://github.com/trabucayre/openFPGALoader) (programming)

## Build and Program

```bash
python3 wishBoneBlink.py
```

This will synthesize the design, run place & route, and program the FPGA via JTAG.

## Hardware

- **Board**: Olimex GateMate A1-EVB
- **FPGA**: Cologne Chip GateMate CCGM1A1
- **LED**: `user_led_n` (active low, accent LED on pin IO_SB_B6)
- **Button**: `user_btn_n` (active low)

## Usage

1. Run the script to build and program the FPGA
2. Press and hold the user button - the LED blinks
3. Release the button - the LED turns off
