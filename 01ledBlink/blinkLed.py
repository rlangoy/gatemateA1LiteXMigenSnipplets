
"""
LED blink — Migen module that blinks an LED using a free-running counter.

Counter bit 23 drives the LED, producing a visible blink rate
at 10 MHz clock (2^23 ≈ 8.4 M cycles → ~0.84 s half-period).

Build:  python blinkLed.py
"""

from migen import *
from  litex_boards.targets.olimex_gatemate_a1_evb import *


# Create:
#+-----------------------------+
#|   Blink (Module)            |
#|     - 26-bit free counter   |
#|     - bit 23 → LED          |
#+-----------------------------+
class Blink(Module):
    """LED blink module. Bit 23 of a free-running counter drives the LED."""

    def __init__(self, led):
        counter = Signal(26)

        # Combinatorial assignment: wire counter bit 23 directly to the LED pin
        self.comb += led.eq(counter[23])

        # Synchronous assignment: increment counter every clock cycle
        self.sync += counter.eq(counter + 1)


# ------------------
# Build The System
# ------------------
def main():    
    import os
    
    # Initialize the platform with pin/IO definitions
    platform = olimex_gatemate_a1_evb.Platform()
    
    # Get LED signal from platform
    led = platform.request("user_led_n", 0)

    # Instantiate top-level module
    module = Blink(led)

    # get the build directory
    build_dir = os.getcwd() + "/build"

    # Synthesize and place-and-route via the Cologne Chip toolchain
    platform.build(module, build_dir)

    # program the chip
    platform.create_programmer().load_bitstream(build_dir + "/top_00.cfg")

if __name__ == "__main__":
    main()
