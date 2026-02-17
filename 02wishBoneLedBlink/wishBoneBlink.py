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


class WishboneLed(Module):
    """Wishbone slave with built-in address decoding.

    Always ACKs every transaction to prevent bus hangs on unmapped addresses.
    Only updates the LED register for writes to the 0x40000000 region.
    """

    def __init__(self, led):
        self.bus = wishbone.Interface(data_width=32, adr_width=30)
        led_reg = Signal()
        addr_match = Signal()

        # Address decode: byte addr 0x40000000 = word addr 0x10000000
        self.comb += addr_match.eq(self.bus.adr[26:30] == ADDR_LED_REGION)

        # Always ACK every transaction — prevents bus hang on unmapped access
        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.cyc & self.bus.stb & ~self.bus.ack,
                self.bus.ack.eq(1),
                If(self.bus.we & addr_match,
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


class Top(Module):
    def __init__(self, platform):
        led = platform.request("user_led_n", 0)
        serial = platform.request("serial")

        # UART Wishbone bridge — host PC becomes bus master
        self.submodules.bridge = bridge = UARTWishboneBridge(
            pads=serial, clk_freq=CLK_FREQ, baudrate=BAUDRATE,
        )

        # LED peripheral — direct connection, address decoding is internal
        self.submodules.led = led_periph = WishboneLed(led)
        self.comb += bridge.wishbone.connect(led_periph.bus)


platform = olimex_gatemate_a1_evb.Platform()

# get the build directory
build_dir = os.getcwd() + "/build"

# build the design
platform.build(Top(platform), build_dir)

# program the chip
platform.create_programmer().load_bitstream(build_dir + "/top_00.cfg")
