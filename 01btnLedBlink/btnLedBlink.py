from migen import *
from  litex_boards.targets.olimex_gatemate_a1_evb import *
#from litex_boards.platforms import colognechip_gatemate_evb 

# create a led blinker module
class Blink(Module):
    def __init__(self, led,btn):
        counter = Signal(26)

        # synchronous assignement
        self.sync += counter.eq(counter + 1)

        # combinatorial assignment
        self.comb += If(btn == 0,            # If the user-button is  pressed (btn=0): blink using counter bit
                        led.eq(counter[23])  #   set led ("user_led_n", 0) =  counter-bit23 
        ).Else(                              # If the user-button is not pressed
            led.eq(1)                        #:  set led ("user_led_n", 0) = 1   ( turn LED off )
        )

# create/init  the development platform
platform = olimex_gatemate_a1_evb.Platform()

# get led signal from our platform
led = platform.request("user_led_n", 0)
btn = platform.request("user_btn_n",0)

# create our main module
module = Blink(led,btn)

# get the build directory
import os
build_dir=os.getcwd()+"/build"
# build the defign
platform.build(module, build_dir)

#program the chip
platform.create_programmer().load_bitstream(build_dir + "/top_00.cfg")
