"""
Button → LED — minimal LiteX/Migen design for the GateMate A1 EVB.

Pressing the button drives the LED directly (combinational, active-low).

Build:   python btn2Led.py
Program: openFPGALoader --cable dirtyJtag build/top_00.cfg

Note:
  The _io list and Platform class below can be replaced by importing
  the upstream board definition:
      from litex_boards.platforms import olimex_gatemate_a1_evb
"""

from migen import *
from litex.build.generic_platform import Pins, Misc, Subsignal
from litex.build.colognechip.platform import CologneChipPlatform


# ---------------------------------------------------------------------
# Minimal GateMate A1 EVB platform definition
# (superseded by litex_boards.platforms.olimex_gatemate_a1_evb)
# ---------------------------------------------------------------------
_io = [
    ("clk0",       0, Pins("IO_SB_A8")),
    ("user_led_n", 0, Pins("IO_SB_B6")),
    ("user_btn_n", 0, Pins("IO_SB_B7")),
]

class Platform(CologneChipPlatform):
    default_clk_name   = "clk0"
    default_clk_period = 1e9 / 10e6  # 10 MHz

    def __init__(self):
        CologneChipPlatform.__init__(self, "CCGM1A1", _io, toolchain="colognechip")


# Create:
#+----------------------------------+
#|   Btn2Led (combinational module) |
#|     - btn_n -> led_n (direct)    |
#|     - button pressed  → LED on   |
#|     - button released → LED off  |
#+----------------------------------+
class Btn2Led(Module):
    """Combinational button-to-LED module. Drives LED directly from button signal."""

    def __init__(self, led, btn):
        # Both signals are active-low: pass btn straight through to led
        self.comb += led.eq(btn)


# ------------------
# Build The System
# ------------------
def main():
    import os, subprocess

    # Initialize the platform with pin/IO definitions
    platform = Platform()

    # Request named signals from the platform configuration
    led = platform.request("user_led_n", 0)
    btn = platform.request("user_btn_n", 0)

    # Instantiate the top-level module
    module = Btn2Led(led, btn)

    # Synthesize and place-and-route via the Cologne Chip toolchain
    build_dir = os.getcwd() + "/build"
    platform.build(module, build_dir, run=True)

    # Program the bitstream onto the FPGA
    subprocess.run(["openFPGALoader", "--cable", "dirtyJtag", "build/top_00.cfg"], check=True)

if __name__ == "__main__":
    main()
