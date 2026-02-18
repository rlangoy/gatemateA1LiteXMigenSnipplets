from migen import *
from litex.soc.interconnect import wishbone
from litex_boards.platforms import olimex_gatemate_a1_evb

# LED blinker module as a Wishbone slave peripheral
class WishboneBlink(Module):
    def __init__(self, led):
        # Create a Wishbone slave interface
        self.bus = bus = wishbone.Interface()

        # Register to hold the enableBlinking flag (bit 0 of wishbone data)
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

        # Free-running counter for blinking
        counter = Signal(26)
        self.sync += counter.eq(counter + 1)

        # LED control: blink when enabled, LED off when disabled
        self.comb += If(enableBlinking,
            led.eq(counter[23])
        ).Else(
            led.eq(1)                   # led_n=1 means LED off (active low)
        )

# Simple Wishbone master: writes enableBlinking based on button state
class WishboneMaster(Module):
    def __init__(self, btn):
        # Create a Wishbone master interface
        self.bus = bus = wishbone.Interface()

        # Detect button press edge (active low button)
        btn_d = Signal()
        btn_rise = Signal()
        btn_fall = Signal()
        self.sync += btn_d.eq(btn)
        self.comb += [
            btn_fall.eq(btn_d & ~btn),   # button pressed  (1->0 transition)
            btn_rise.eq(~btn_d & btn),   # button released (0->1 transition)
        ]

        # State machine to issue Wishbone writes on button edges
        self.submodules.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            If(btn_fall,
                NextState("WRITE_ON")
            ).Elif(btn_rise,
                NextState("WRITE_OFF")
            )
        )
        fsm.act("WRITE_ON",
            bus.cyc.eq(1),
            bus.stb.eq(1),
            bus.we.eq(1),
            bus.dat_w.eq(1),            # enable blinking
            If(bus.ack,
                NextState("IDLE")
            )
        )
        fsm.act("WRITE_OFF",
            bus.cyc.eq(1),
            bus.stb.eq(1),
            bus.we.eq(1),
            bus.dat_w.eq(0),            # disable blinking
            If(bus.ack,
                NextState("IDLE")
            )
        )

# Top-level module connecting master and slave via Wishbone bus
class Top(Module):
    def __init__(self, platform):
        # Get I/O signals from platform
        led = platform.request("user_led_n", 0)
        btn = platform.request("user_btn_n", 0)

        # Instantiate Wishbone slave (LED blinker) and master (button controller)
        self.submodules.blink  = blink  = WishboneBlink(led)
        self.submodules.master = master = WishboneMaster(btn)

        # Connect master to slave
        self.comb += master.bus.connect(blink.bus)

# create/init the development platform
platform = olimex_gatemate_a1_evb.Platform()

# create the top module
top = Top(platform)

# build the design
import os
build_dir = os.path.join(os.getcwd(), "build")
platform.build(top, build_dir=build_dir)

# program the chip
platform.create_programmer().load_bitstream(os.path.join(build_dir, "top_00.cfg"))
