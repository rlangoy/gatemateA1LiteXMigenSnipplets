#!/usr/bin/env python3
"""
Wishbone LED blink — UART bridge with address-decoded LED peripheral.

The host PC acts as bus master via UART Wishbone bridge.
LED peripheral is mapped at 0x40000000 (bit 0 controls the LED).

Address decoding is handled inside the slave: every transaction gets an ACK
(preventing bus hangs per https://github.com/enjoy-digital/litex/issues/82),
but only writes to the 0x40000000 region update the LED register.

Build:  python wishBoneBlink.py
Server: litex_server --uart --uart-port=/dev/ttyUSBx
Control: python ledControl.py
"""

import os

from migen import *
from litex.soc.interconnect import wishbone
from litex.soc.cores.uart import UARTWishboneBridge
from litex_boards.platforms import olimex_gatemate_a1_evb

CLK_FREQ = int(10e6)
BAUDRATE = 115200

# Word address for 0x40000000 region: top 4 bits of 30-bit word address
ADDR_LED_REGION = 0b0100


#Create:
#+-------------------------------------+
#|   WishboneLed (Wishbone slave)      |
#|     - Always ACKs every address     |
#|     - Only writes reg at 0x40000000 |
#|     - bit 0 -> LED                  |
#+-------------------------------------+
class WishboneLed(Module):
    """Wishbone slave with built-in address decoding.

    Always ACKs every transaction to prevent bus hangs on unmapped addresses.
    Only updates the LED register for writes to the 0x40000400 address.
    """

    def __init__(self, led):
        self.bus = wishbone.Interface(data_width=32, adr_width=30)
        
        led_reg = Signal()      # Output signal from the wishbone
        addr_match = Signal()   # True if 0x40000000 
              
        # Wishbone (as used by LiteX) uses WORD addressing, not byte addressing.
        # convert 0x40000400 byte-addr to word address (0x40000400 >> 2) = 0x10000100
        #      Address decode: byte addr 0x40000000 = word addr 0x10000000
        LED_WORD_ADDR = 0x10000100  
        self.comb += addr_match.eq(self.bus.adr == LED_WORD_ADDR) # addr_match = True if bus.adr= 0x40000000

        # Evaluaton and updation the block on the rising edge of the system clock
        self.sync += [
            # WishBone bus, Default: deassert ACK every clock cycle (active for only one cycle)
            self.bus.ack.eq(0),
        
            # Wait for WishBone bus-ready (CYC and STB both asserted, ACK not yet given) 
            # CYC (Cycle) indicates that a valid bus cycle is in progress.
            # STB (Strobe) indicates that the master is presenting valid address and data on the bus 
            If(self.bus.cyc & self.bus.stb & ~self.bus.ack,
                
                # WishBone bus-ready                    
                # Respond that the HW is ready (to the bus master by asserting ACK for one cycle)
                self.bus.ack.eq(1),                
                
                # :: Warning ::
                # Unmatched address → is ACK and so bus would hang  not hang if user acces wrong address region
                #   Problem We ACK addresses that does not belog to us (might cause timing issues)

                # If this is a write transaction (WE asserted) and the bus-address matches 0x40000400
                If(self.bus.we & addr_match,                  
                    # Latch the least-significant bit of the write data bus into the LED register
                    led_reg.eq(self.bus.dat_w[0]),
                ),
            ),
        ]
        
        self.comb += [
            If(addr_match,
                self.bus.dat_r.eq(led_reg),
            ).Else(
                self.bus.dat_r.eq(0),
            ),
            led.eq(~led_reg),  # active-low: reg=1 → LED on
        ]



# Create:
#+------------------------------------+
#| UARTWishboneBridge                 |
#|   (Wishbone master)                |
#|        |                           |
#|        | Wishbone bus (direct)     |
#|        v                           |
#|   WishboneLed (slave)              |
#+------------------------------------+
class Top(Module):
    def __init__(self, platform):
        
        #Get the user I/O pin numbers from litex_boards.platforms.olimex_gatemate_a1_evb
        led = platform.request("user_led_n", 0)
        
        #Get the UART I/O pins numbers from litex_boards.platforms.olimex_gatemate_a1_evb
        serial = platform.request("serial")

        # Create a USRT that is connected to the WishBoneBus
        # UART Wishbone bridge — host PC becomes bus master
        self.submodules.bridge = bridge = UARTWishboneBridge(
            pads=serial, clk_freq=CLK_FREQ, baudrate=BAUDRATE,
        )

        # Connect the module led
        # LED peripheral — direct connection, address decoding is internal
        # Create the WishboneLed module led_priph and add it to the submodules
        self.submodules.led = led_periph = WishboneLed(led)
        #connect the WishboneLed module to the WishBoneBus
        self.comb += bridge.wishbone.connect(led_periph.bus)


platform = olimex_gatemate_a1_evb.Platform()

# get the build directory
build_dir = os.getcwd() + "/build"

# build the design
platform.build(Top(platform), build_dir)

# program the chip
platform.create_programmer().load_bitstream(build_dir + "/top_00.cfg")