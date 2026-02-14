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

### 1. ledBlink

A minimal LED blinker demonstrating the basics of Migen/LiteX development. This project shows how to:
- Create a simple counter-based LED blinker
- Use the Migen Module class
- Access platform resources (LEDs)
- Build and program the FPGA

**Features:**
- 26-bit counter increments on the 10 MHz clock
- Bit 25 toggles the user LED approximately every ~3.4 seconds
- Complete build and programming instructions

**Location**: [`ledBlink/`](./ledBlink/)

See the [ledBlink README](./ledBlink/README.md) for detailed build and programming instructions.

## Prerequisites

To work with these examples, you'll need:

- **Python 3** with the following packages:
  - [LiteX](https://github.com/enjoy-digital/litex)
  - [Migen](https://github.com/m-labs/migen)
- **Yosys** - for synthesis
- **Cologne Chip p_r** - place-and-route toolchain
- **openFPGALoader** - for programming the FPGA
- **JTAG adapter** - such as DirtyJTAG or compatible

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
├── README.md           # This file
└── ledBlink/          # LED blinker example
    ├── README.md      # Detailed project documentation
    └── blinkLed.py    # Migen/LiteX source code
```

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests to add more examples or improve existing ones.

## License

Please refer to individual project directories for licensing information.

## Resources

- [LiteX GitHub](https://github.com/enjoy-digital/litex)
- [Migen GitHub](https://github.com/m-labs/migen)
- [GateMateA1-EVB Hardware](https://github.com/OLIMEX/GateMateA1-EVB)
- [Cologne Chip](https://www.colognechip.com/)
