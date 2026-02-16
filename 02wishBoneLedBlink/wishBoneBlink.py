from migen import *
from migen.bus import wishbone
from litex.soc.integration.soc import SoCMini, SoCRegion
from litex.soc.integration.builder import Builder
from  litex_boards.targets.olimex_gatemate_a1_evb import *
#from litex_boards.platforms import colognechip_gatemate_evb

# create a led blinker module as a Wishbone peripheral
class Blink(Module):
    def __init__(self, led):
        #Create a wish bone interface
        self.bus = bus = wishbone.Interface()

        #Connect the signal enableBlinking to  bit 0 of the implemented wishbone bus
        enableBlinking = Signal()

        # Wishbone slave logic: handle writes and reads
        self.sync += [
            bus.ack.eq(0),
            If(bus.cyc & bus.stb & ~bus.ack,
                bus.ack.eq(1),
                If(bus.we,
                    enableBlinking.eq(bus.dat_w[0])
                )
            )
        ]
        self.comb += bus.dat_r.eq(enableBlinking)

        counter = Signal(26)

        # synchronous assignement
        self.sync += counter.eq(counter + 1)

        # combinatorial assignment
        self.comb += If(enableBlinking  == 1,   # If the enableBlinking bit is set     : blink using counter bit
            led.eq(counter[23])
        ).Else(
            led.eq(1)                           # If the enableBlinking bit is not set : led_n=1 means LED off
        )

# SoC wrapping the Blink peripheral with a Wishbone address mapping
class BlinkSoC(SoCMini):
    def __init__(self, platform):
        SoCMini.__init__(self, platform, clk_freq=10e6)

        # get led signal from our platform
        led = platform.request("user_led_n", 0)

        # create our Blink peripheral and map it at address 0x30000000
        self.submodules.blink = Blink(led)
        self.bus.add_slave("blink", self.blink.bus, region=SoCRegion(origin=0x30000000, size=0x1000))

# create/init  the development platform
platform = olimex_gatemate_a1_evb.Platform()

# create the SoC
soc = BlinkSoC(platform)

# get the build directory
import os
build_dir=os.getcwd()+"/build"
# build the design
builder = Builder(soc, output_dir=build_dir)
builder.build()

#program the chip
platform.create_programmer().load_bitstream(build_dir + "/gateware/top_00.cfg")
