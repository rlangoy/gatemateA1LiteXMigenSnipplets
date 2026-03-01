
#!/usr/bin/env python3

# -------------------------------------------------
# Target: Olimex GateMate A1 EVB
# replacement for olimex_gatemate_a1_evb.py with hardened UART TX path
#   ( python3 -m litex_boards.targets.olimex_gatemate_a1_evb )
#
# Extends BaseSoC with a hardened UART TX path (via uart_tx_hardened.py):
#   - Replaces the standard RS232PHY with RS232PHYPatched
#   - Inlines the bit-timing loop to avoid GateMate toolchain inference issues
#
# All original target options are preserved (video, ethernet, SDCard, etc.)
#
# Usage:
#   python3 gateMateHardenedTxUart.py --help
#   python3 gateMateHardenedTxUart.py --cpu-type picorv32 --cpu-variant minimal --build --load
# -------------------------------------------------

from litex_boards.targets.olimex_gatemate_a1_evb import BaseSoC
from litex_boards.platforms import olimex_gatemate_a1_evb
from litex.soc.integration.builder import Builder
from litex.build.parser import LiteXArgumentParser

# make_uart_tx_hardened(BaseSoC) returns a subclass of BaseSoC that overrides
# add_uart() to install RS232PHYPatched instead of the standard RS232PHY.
# Python MRO ensures the override is called when BaseSoC.__init__ internally
# invokes self.add_uart(), so no post-init patching is needed.
from uart_tx_hardened import make_uart_tx_hardened

# -------------------------------------------------
# Custom SoC
# -------------------------------------------------
BaseSocUartTxHardened = make_uart_tx_hardened(BaseSoC)

class MySoC(BaseSocUartTxHardened):
    def __init__(self, **kwargs):
        BaseSocUartTxHardened.__init__(self, **kwargs)

# -------------------------------------------------
# Build & Flash
# -------------------------------------------------
def main():
    parser = LiteXArgumentParser(platform=olimex_gatemate_a1_evb.Platform, description="LiteX SoC on Olimex GateMate A1 EVB (hardened UART TX)")
    parser.add_target_argument("--sys-clk-freq",        default=24e6, type=float, help="System clock frequency.")
    parser.add_target_argument("--with-video-terminal", action="store_true",      help="Enable Video Terminal (VGA).")
    parser.add_target_argument("--flash",               action="store_true",      help="Flash bitstream.")
    pmodopts = parser.target_group.add_mutually_exclusive_group()
    pmodopts.add_argument("--with-spi-sdcard",          action="store_true",      help="Enable SPI-mode SDCard support.")
    pmodopts.add_argument("--with-sdcard",              action="store_true",      help="Enable SDCard support.")
    pmodopts.add_argument("--with-ethernet",            action="store_true",      help="Enable Ethernet support.")
    pmodopts.add_argument("--with-etherbone",           action="store_true",      help="Enable Etherbone support.")
    parser.add_target_argument("--eth-ip",              default="192.168.1.50",   help="Ethernet/Etherbone IP address.")
    parser.add_target_argument("--eth-dynamic-ip",      action="store_true",      help="Enable dynamic Ethernet IP addresses setting.")
    parser.add_target_argument("--remote-ip",           default="192.168.1.100",  help="Remote IP address of TFTP server.")

    args = parser.parse_args()

    soc = MySoC(
        sys_clk_freq        = args.sys_clk_freq,
        toolchain           = args.toolchain,
        with_video_terminal = args.with_video_terminal,
        with_ethernet       = args.with_ethernet,
        with_etherbone      = args.with_etherbone,
        eth_ip              = args.eth_ip,
        eth_dynamic_ip      = args.eth_dynamic_ip,
        remote_ip           = args.remote_ip,
        **parser.soc_argdict)

    soc.platform.add_extension(olimex_gatemate_a1_evb._pmods_io)
    if args.with_spi_sdcard:
        soc.add_spi_sdcard()
    if args.with_sdcard:
        soc.add_sdcard()

    builder = Builder(soc, **parser.builder_argdict)
    if args.build:
        builder.build(**parser.toolchain_argdict)

    if args.load:
        prog = soc.platform.create_programmer()
        prog.load_bitstream(builder.get_bitstream_filename(mode="sram"))

    if args.flash:
        prog = soc.platform.create_programmer()
        prog.flash(0, builder.get_bitstream_filename(mode="flash"))

if __name__ == "__main__":
    main()
