from migen import *
from litex.soc.interconnect import wishbone
from litex.soc.cores.uart import UARTWishboneBridge
from litex_boards.platforms import olimex_gatemate_a1_evb

# LED peripheral as a Wishbone slave
# Bit 0 of the data word controls the LED at address 0x40000000
class WishboneLed(Module):
    def __init__(self, led):
        self.bus = bus = wishbone.Interface()

        # 1-bit register: LED state (active low on this board)
        led_reg = Signal()

        # Wishbone slave logic
        self.sync += [
            bus.ack.eq(0),
            If(bus.cyc & bus.stb & ~bus.ack,
                bus.ack.eq(1),
                If(bus.we,
                    led_reg.eq(bus.dat_w[0])
                )
            )
        ]
        self.comb += [
            bus.dat_r.eq(led_reg),
            led.eq(~led_reg),  # active-low LED: reg=1 -> led_n=0 -> LED on
        ]

# Top-level module: UART bridge master connected to LED slave
class Top(Module):
    def __init__(self, platform):
        led = platform.request("user_led_n", 0)

        # UART Wishbone bridge — host PC becomes the bus master
        serial_pads = platform.request("serial")
        self.submodules.bridge = bridge = UARTWishboneBridge(
            pads     = serial_pads,
            clk_freq = int(10e6),    # 10 MHz oscillator on the board
            baudrate = 115200,
        )

        # LED peripheral (Wishbone slave)
        self.submodules.led = led_periph = WishboneLed(led)

        # Connect bridge master to LED slave (point-to-point, single slave)
        self.comb += bridge.wishbone.connect(led_periph.bus)

# Build
platform = olimex_gatemate_a1_evb.Platform()
top = Top(platform)

import os
build_dir = os.path.join(os.getcwd(), "build")
platform.build(top, build_dir=build_dir)
