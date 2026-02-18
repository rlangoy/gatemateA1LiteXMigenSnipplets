from migen import *
from litex.build.generic_platform import Pins, Misc, Subsignal
from litex.build.colognechip.platform import CologneChipPlatform

# ---------------------------------------------------------------------
# Minimal GateMateA1-evb platform ()
# The _io and Platform Class sound be obmitteed by including the library
#        from litex_boards.platforms import olimex_gatemate_a1_evb
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
# -------------------------------------------------
# Button → LED module
# -------------------------------------------------
class Btn2Led(Module):
    def __init__(self, led, btn):
        self.comb += led.eq(btn)

# ------------------
# Build The System
# ------------------
def main():
    import os,subprocess
    
    # Initaialize the FPGA and I/O defs
    platform = Platform()
    
    # Get the signals from the platform config 
    led = platform.request("user_led_n", 0)
    btn = platform.request("user_btn_n", 0)

    #Create the Module Blink
    module = Btn2Led(led, btn)

    # Build the design
    build_dir = os.getcwd() + "/build"
    platform.build(module, build_dir, run=True)
  
    # program the chip
    subprocess.run([ "openFPGALoader", "--cable", "dirtyJtag", "build/top_00.cfg" ], check=True)
    
if __name__ == "__main__":
    main()
