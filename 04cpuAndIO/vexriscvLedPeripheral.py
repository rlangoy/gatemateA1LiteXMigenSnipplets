#!/usr/bin/env python3

from migen import *
from litex_boards.targets.olimex_gatemate_a1_evb import BaseSoC
from litex_boards.platforms import olimex_gatemate_a1_evb

from litex.soc.integration.builder import Builder
from litex.soc.integration.soc_core import soc_core_args, soc_core_argdict
from litex.soc.interconnect.csr import AutoCSR, CSRStorage
import argparse


# -------------------------------------------------
# AutoCSR LED Peripheral
# -------------------------------------------------
class LedPeripheral(Module, AutoCSR):
    def __init__(self, led):
        self.control = CSRStorage(1, name="control", description="LED control (bit 0: 1=on, 0=off)")
        self.comb += led.eq(~self.control.storage)


# -------------------------------------------------
# Custom SoC
# -------------------------------------------------
class MySoC(BaseSoC):
    def __init__(self, **kwargs):
        kwargs.setdefault("cpu_type", "vexriscv")
        kwargs.setdefault("uart_baudrate", 115200)
        kwargs.setdefault("integrated_rom_size", 0x8000)  # 32KB BIOS ROM at CPU reset address 0x00000000

        BaseSoC.__init__(self,
            with_led_chaser=False,     # Disable chaser so we can claim user_led_n ourselves
            **kwargs
        )

        platform = self.platform

        # Request physical LED from platform (active-low: _n suffix)
        led = platform.request("user_led_n", 0)

        # Instantiate peripheral
        self.submodules.led_peripheral = LedPeripheral(led)

        # Register as CSR
        self.add_csr("led_peripheral")


# -------------------------------------------------
# Build & Flash
# -------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    soc_core_args(parser)
    args = parser.parse_args()

    soc = MySoC(**soc_core_argdict(args))
    builder = Builder(soc, output_dir="build", compile_gateware=True, compile_software=True)
    builder.build()

    # Flash bitstream to FPGA SRAM via dirtyJtag
    prog = soc.platform.create_programmer()
    prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))


if __name__ == "__main__":
    main()
