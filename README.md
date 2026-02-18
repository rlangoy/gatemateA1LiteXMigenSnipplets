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

### 1. 00ledBlink

A minimal LED blinker demonstrating the basics of Migen/LiteX development. This project shows how to:
- Create a simple counter-based LED blinker
- Use the Migen Module class
- Access platform resources (LEDs)
- Build and program the FPGA

**Features:**
- 26-bit counter increments on the 10 MHz clock
- Bit 23 toggles the user LED approximately every ~1.2 seconds
- Complete build and programming instructions

**Location**: [`00ledBlink/`](./00ledBlink/)

See the [00ledBlink README](./00ledBlink/README.md) for detailed build and programming instructions.

### 2. 01btnLedBlink

An LED blinker controlled by a user button. The LED toggles every ~1.2 seconds only while the button is held.

**Location**: [`01btnLedBlink/`](./01btnLedBlink/)

See the [01btnLedBlink README](./01btnLedBlink/README.md) for details.

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

2. Navigate to a project directory (e.g., `ledBlink`)

3. Follow the project-specific README for build and programming instructions

## Project Structure

```
.
├── README.md                        # This file
├── 00ledBlink/                      # LED blinker example
│   ├── README.md
│   └── blinkLed.py
├── 01btnLedBlink/                   # Button-controlled LED blinker
│   ├── README.md
│   └── btnLedBlink.py
└── 02wishBoneMasterAndPerrial/      # Wishbone LED control via UART
    ├── README.md
    ├── uartWishBoneDirectMapingLed.py
    ├── uartWishBoneCrsLed.py
    ├── wbTestLedModule.py
    └── test_address_decode.py
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
