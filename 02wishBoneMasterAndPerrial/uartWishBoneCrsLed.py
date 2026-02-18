
"""
CSR LED blink — LiteX SoCMini with UART bridge and CSR-mapped LED peripheral.

The host PC acts as bus master via UART Wishbone bridge.
LED is controlled via a CSR register (bit 0).

Build:  python uartWishBoneCrsLed.py
Server: litex_server --uart --uart-port=/dev/ttyUSBx

Register map:
  Address = csr_base (mem_map) + csr_location (csr_map) × csr_paging
  ctrl        : location 0 → 0x40000000
  led_control : location 1 → 0x40000400

  Verify against build/csr.csv after building.
  
  Gatecount:    726       olimex_gatemate_a1_evb_00.v
"""

import os

from migen import *
from litex.soc.integration.soc_core import SoCMini
from litex.soc.integration.builder import Builder
from litex.soc.interconnect.csr import AutoCSR, CSRStorage
from litex_boards.platforms import olimex_gatemate_a1_evb

CLK_FREQ = int(10e6)
BAUDRATE = 115200


# Create:
#+--------------------------------------------+
#|   LedPeripheral (AutoCSR peripheral)       |
#|     - 1-bit CSR storage register           |
#|     - "control" register at 0x40000400     |
#|     - bit 0 -> LED (active low)            |
#+--------------------------------------------+
class LedPeripheral(Module, AutoCSR):
    """CSR-mapped LED peripheral. Bit 0 of the control register drives the LED."""

    def __init__(self, led):
        # 1-bit CSR register, directly accessible from the host via litex_server
        self.control = CSRStorage(1, name="control", description="LED control (bit 0: 1=on, 0=off)")

        # Active-low LED: reg=1 → pin driven low → LED on
        self.comb += led.eq(~self.control.storage)



# Create:
#+------------------------------------+
#| SoCMini (Top)                      |
#|                                    |
#|  UARTWishboneBridge (bus master)   |
#|        |                           |
#|        | Wishbone bus              |
#|        v                           |
#|    CSR decoder                     |
#|        |                           |
#|        v                           |
#|  LedPeripheral (CSR slave)         |
#|    @ 0x40000400                    |
#+------------------------------------+
class Top(SoCMini):
    # Set CSR region base address to 0x40000000
    mem_map = {
        **SoCMini.mem_map,
        "csr": 0x40000000,
    }

    # Explicitly assign CSR location slots per peripheral
    # Address = 0x40000000 + location × 0x400
    csr_map = {
        "ctrl": 0,   # 0x40000000
        "led":  1,   # 0x40000400
    }

    def __init__(self, platform):
        # Initialize SoCMini with UART Wishbone bridge as the bus master.
        SoCMini.__init__(
            self,
            platform,
            clk_freq=CLK_FREQ,
            uart_name="crossover",
            csr_address_width=14,
            csr_paging=0x400,
        )

        # UART-to-Wishbone bridge — host PC becomes bus master
        from litex.soc.cores.uart import UARTWishboneBridge
        serial = platform.request("serial")
        self.submodules.bridge = UARTWishboneBridge(
            pads=serial, clk_freq=CLK_FREQ, baudrate=BAUDRATE,
        )
        self.bus.add_master(name="bridge", master=self.bridge.wishbone)

        # LED peripheral — auto-registered as CSR peripheral via AutoCSR
        led_pin = platform.request("user_led_n", 0)
        self.submodules.led = LedPeripheral(led_pin)


# ------------------
# Build  The System 
# ------------------
def main():

	#Select dev-board to run the example
	platform = olimex_gatemate_a1_evb.Platform()
	soc = Top(platform)

	# Use Builder to generate csr.csv and other exports
	builder = Builder(soc, output_dir="build", compile_gateware=True, compile_software=False)
	builder.build()

	# Program the chip
	platform.create_programmer().load_bitstream("build/gateware/olimex_gatemate_a1_evb_00.cfg")

if __name__ == "__main__":
    main()
