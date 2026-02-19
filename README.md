# GateMate A1 LiteX/Migen Snippets

A collection of example projects demonstrating LiteX and Migen development for the Cologne Chip GateMate CCGM1A1 FPGA.

## Overview

This repository contains practical examples and code snippets for working with the GateMate FPGA using the LiteX/Migen hardware description framework. These examples are designed to help you get started with FPGA development on this platform.

## Hardware

The examples in this repository target the **GateMateA1-EVB** development board:
- **Board**: [OLIMEX GateMateA1-EVB](https://github.com/OLIMEX/GateMateA1-EVB) (Open Hardware)
- **FPGA**: Cologne Chip CCGM1A1
- **Clock**: 10 MHz on-board oscillator

## Projects

### 1. 00btn2Led

A minimal button-to-LED example demonstrating pure combinatorial logic with Migen/LiteX. This project shows how to:
- Create a Migen module with combinatorial logic
- Wire a button directly to an LED with no clock or state
- Use the Migen Module class
- Access platform resources (buttons and LEDs)
- Build and program the FPGA

**Features:**
- Pure combinatorial logic - no clock domain required
- Button directly controls LED state (active low)
- LED mirrors button instantly
- Complete build and programming instructions

**Location**: [`00btn2Led/`](./00btn2Led/)

See the [00btn2Led README](./00btn2Led/README.md) for detailed build and programming instructions.

### 2. 01ledBlink

A minimal LED blinker demonstrating the basics of Migen/LiteX development with clocked logic. This project shows how to:
- Create a simple counter-based LED blinker
- Use the Migen Module class with synchronous logic
- Access platform resources (LEDs)
- Build and program the FPGA

**Features:**
- 26-bit counter increments on the 10 MHz clock
- Bit 23 toggles the user LED approximately every ~0.84 seconds
- Complete build and programming instructions

**Location**: [`01ledBlink/`](./01ledBlink/)

See the [01ledBlink README](./01ledBlink/README.md) for details.

### 3. 02wishBoneMasterAndPerrial

Demonstrates controlling an LED from a host PC over UART using a Wishbone bus. Shows how to:
- Create a Wishbone slave peripheral (a 1-bit LED register)
- Use LiteX's `UARTWishboneBridge` to expose the Wishbone bus
- Control the peripheral from host-side Python using `RemoteClient`

**Features:**
- LED mapped to bit 0 at address `0x40000400`
- Two FPGA design variants: direct address mapping and CSR-based
- Simulation testbench for address decoding verification

**Location**: [`02wishBoneMasterAndPerrial/`](./02wishBoneMasterAndPerrial/)

See the [02wishBoneMasterAndPerrial README](./02wishBoneMasterAndPerrial/README.md) for details.

### 4. 03wishBoneCsrHdl

Demonstrates wrapping an HDL module (VHDL or Verilog) as a Migen black-box and connecting it to the Wishbone bus using LiteX CSR registers. Implements a CRC32 peripheral backed by a generated HDL step entity. Shows how to:
- Wrap a VHDL/Verilog entity as a Migen `Instance` (black-box)
- Build a CSR-mapped peripheral exposing hardware logic via two 32-bit registers
- Use LiteX's `UARTWishboneBridge` and `RemoteClient` for host-side control
- Synthesise VHDL sources with Yosys via the GHDL plugin

**Features:**
- CRC32 accumulator conforming to CRC-32/ISO-HDLC (PKZIP standard)
- Two FPGA design variants: Verilog black-box (`wishBoneCrsCrc32Verilog.py`) and VHDL black-box (`wishBoneCrsCrc32Vhdl.py`)
- Host-side hardware validation script and simulation testbench
- One-time GHDL Yosys plugin setup for synthesising VHDL (no root access required)

**Location**: [`03wishBoneCsrHdl/`](./03wishBoneCsrHdl/)

See the [03wishBoneCsrHdl README](./03wishBoneCsrHdl/README.md) for details.

## Prerequisites
Install: <br> 
- LiteX <br>
- ToolChain for FPGA. <br>
- RISCV-V prosessor PicoRV32 (optional) <br>
 Ubuntu 24.04, Install instruction for [GateMateA1-EVB](https://github.com/rlangoy/gatemateA1LiteXMigenSnipplets/blob/main/doc/litex_picorv32_gatemate_a1_e.md)

## Getting Started

1. Clone this repository:
   ```bash
   git clone https://github.com/rlangoy/gatemateA1LiteXMigenSnipplets.git
   cd gatemateA1LiteXMigenSnipplets
   ```

2. Navigate to a project directory (e.g., `00btn2Led`, `01ledBlink`, `02wishBoneMasterAndPerrial`, or `03wishBoneCsrHdl`)

3. Follow the project-specific README for build and programming instructions

## Project Structure

```
.
├── README.md                        # This file
├── 00btn2Led/                       # Button to LED (combinatorial logic)
│   ├── README.md
│   └── btn2Led.py
├── 01ledBlink/                      # LED blinker example
│   ├── README.md
│   └── blinkLed.py
├── 02wishBoneMasterAndPerrial/      # Wishbone LED control via UART
│   ├── README.md
│   ├── designspec.md
│   ├── uartWishBoneDirectMapingLed.py
│   ├── uartWishBoneCrsLed.py
│   ├── wishBoneUartDebugLedPeripheralModule.py
│   └── testBenchLedPeripheral.py
├── 03wishBoneCsrHdl/                # CRC32 peripheral via HDL black-box and CSR
│   ├── README.md
│   ├── wishBoneCrsCrc32Verilog.py   # FPGA design (Verilog black-box)
│   ├── wishBoneCrsCrc32Vhdl.py      # FPGA design (VHDL black-box + GHDL plugin)
│   ├── wishBoneUartDebugCRC32PeripheralModule.py  # Host-side validation
│   ├── testBenchCrc32Peripheral.py  # Simulation testbench
│   ├── hdl/
│   │   ├── crc.vhdl                 # Generated VHDL CRC32 step entity
│   │   └── crc.v                    # Generated Verilog CRC32 step module
│   └── tbLib/
│       └── crcLib.py                # Python reference CRC32 implementation
├── doc/                             # Documentation
└── litexPatch/                      # LiteX patches
```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to add more examples or improve existing ones.

## License

This project is licensed under the Creative Commons Attribution 4.0 International License (CC BY 4.0).

You are free to:
- Share — copy and redistribute the material
- Adapt — remix, transform, and build upon the material

Under the following terms:
- Attribution — You must give appropriate credit.

Full license text:
https://creativecommons.org/licenses/by/4.0/
### Notice
- No warranties are given.

## Resources

- [LiteX GitHub](https://github.com/enjoy-digital/litex)
- [Migen GitHub](https://github.com/m-labs/migen)
- [GateMateA1-EVB Hardware](https://github.com/OLIMEX/GateMateA1-EVB)
- [Cologne Chip](https://www.colognechip.com/)
