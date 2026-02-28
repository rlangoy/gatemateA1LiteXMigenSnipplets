
#!/usr/bin/env python3

from migen import *
from litex_boards.targets.olimex_gatemate_a1_evb import BaseSoC

from litex.soc.integration.builder import Builder
from litex.soc.integration.soc_core import soc_core_args, soc_core_argdict
from litex.soc.interconnect.csr import AutoCSR, CSRStorage
import argparse

# Local UART timing patch.
from uart_timing_patch import RS232PHYPatched


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

        # Build base SoC.  Because MySoC overrides add_uart() below, Python's
        # MRO ensures the patched PHY is used when BaseSoC.__init__ calls
        # self.add_uart() — no double-driver, no re-request of "serial" pads.
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

    # ------------------------------------------------------------------
    # Override add_uart so BaseSoC uses RS232PHYPatched instead of the
    # default RS232PHY.  Called automatically by BaseSoC.__init__ via MRO.
    # Non-serial UART types (crossover, jtag_uart, …) are delegated to
    # the parent unchanged.
    # ------------------------------------------------------------------
    def add_uart(self, name="uart", uart_name="serial", uart_pads=None, baudrate=115200,
                 fifo_depth=16, with_dynamic_baudrate=False, rx_fifo_rx_we=False):
        from litex.soc.cores.uart import UART

        # Request serial pads (loose=True: returns None if not present).
        if uart_pads is None:
            uart_pads_name = "serial" if uart_name == "sim" else uart_name
            uart_pads = self.platform.request(uart_pads_name, loose=True)

        # No physical serial pads → delegate to parent for special UART types.
        if uart_pads is None:
            super().add_uart(name=name, uart_name=uart_name, uart_pads=None,
                             baudrate=baudrate, fifo_depth=fifo_depth,
                             with_dynamic_baudrate=with_dynamic_baudrate,
                             rx_fifo_rx_we=rx_fifo_rx_we)
            return

        # Build patched PHY with guard idle bits before the START bit.
        patched_phy = RS232PHYPatched(
            uart_pads,
            clk_freq=int(self.sys_clk_freq),
            baudrate=baudrate,
            with_dynamic_baudrate=with_dynamic_baudrate,
            tx_guard_bits=1,
        )

        uart = UART(patched_phy,
                    tx_fifo_depth=fifo_depth,
                    rx_fifo_depth=fifo_depth,
                    rx_fifo_rx_we=rx_fifo_rx_we)
        self.add_module(name=name, module=uart)

        if rx_fifo_rx_we:
            self.add_config(f"{name}_RX_FIFO_RX_WE", 1)

        if self.irq.enabled:
            self.irq.add(name, use_loc_if_exists=True)
        else:
            self.add_constant("UART_POLLING", check_duplicate=False)


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
