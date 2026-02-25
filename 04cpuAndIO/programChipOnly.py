#!/usr/bin/env python3
# programChipOnly.py
#
# Intent:
#   Flash a pre-built bitstream onto the GateMate A1 EVB FPGA without
#   re-running synthesis or place-and-route.  Useful for rapid iteration
#   when the gateware is already built and only the board needs to be
#   (re-)programmed.
#
# How it works:
#   1. Instantiate the board Platform.  This gives access to board-specific
#      metadata and the programmer configuration without starting a full build.
#   2. Call platform.create_programmer() to get a DirtyJTAG programmer instance.
#      DirtyJTAG is a low-cost USB-JTAG adapter supported by LiteX out of the box.
#   3. Call prog.load_bitstream() with the path to the SRAM bitstream produced
#      by a previous build.  The bitstream is streamed over JTAG into the FPGA's
#      SRAM — volatile, so the design is lost on power cycle.

from litex_boards.platforms import olimex_gatemate_a1_evb

# Path to the bitstream produced by a previous build (e.g. pico32RvLedPeripheral.py)
BITSTREAM = "build/gateware/olimex_gatemate_a1_evb_00.cfg.bit"

def main():
    platform = olimex_gatemate_a1_evb.Platform()   # board definition, no build triggered
    prog = platform.create_programmer()             # DirtyJTAG over USB
    prog.load_bitstream(BITSTREAM)                  # stream bitstream into FPGA SRAM

if __name__ == "__main__":
    main()
