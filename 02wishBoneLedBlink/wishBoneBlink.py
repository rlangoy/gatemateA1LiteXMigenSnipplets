#!/usr/bin/env python3
"""
Wishbone LED blink — UART bridge with address-decoded LED peripheral.

The host PC acts as bus master via UART Wishbone bridge.
LED peripheral is mapped at 0x40000000 (bit 0 controls the LED).

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


class WishboneLed(Module):
    """Single-register Wishbone slave — bit 0 controls an active-low LED."""

    def __init__(self, led):
        self.bus = wishbone.Interface()
        led_reg = Signal()

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.cyc & self.bus.stb & ~self.bus.ack,
                self.bus.ack.eq(1),
                If(self.bus.we,
                    led_reg.eq(self.bus.dat_w[0]),
                ),
            ),
        ]

        self.comb += [
            self.bus.dat_r.eq(led_reg),
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

        # LED peripheral at 0x40000000
        self.submodules.led = led_periph = WishboneLed(led)

        # Address decoder: route 0x40000000 region to LED slave
        # Byte addr 0x40000000 = word addr 0x10000000
        # Check top 4 bits of 30-bit word addr: 0b0100 = 0x40000000 region
        self.submodules.decoder = wishbone.Decoder(
            bridge.wishbone,
            [(lambda addr: addr[26:30] == 0b0100, led_periph.bus)],
        )


platform = olimex_gatemate_a1_evb.Platform()

# get the build directory
import os
build_dir=os.getcwd()+"/build"

# build the defign
platform.build(Top(platform), build_dir)

#program the chip
platform.create_programmer().load_bitstream(build_dir + "/top_00.cfg")


