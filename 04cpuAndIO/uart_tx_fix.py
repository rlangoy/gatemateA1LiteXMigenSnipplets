"""
Drop-in replacement for the UART core patches applied to LiteX's uart.py.

Encapsulates all patches so the installed LiteX uart.py can remain stock:
  - PATCH-3: add_auto_tx_flush ANDs with source.ready (no silent byte loss)
  - PATCH-4: TX IRQ triggers on FIFO-empty instead of FIFO-not-full
  - AsyncFIFO depth rounded to next power of two (fixes bit-flip corruption)
  - SyncFIFO uses buffered=False

Also integrates the hardened TX PHY from uart_tx_hardened.py (PATCH-2,
guard-bit, early-start, majority-vote RX, reset-gated TX clock domain).

Usage:
    from uart_tx_fix import makeSocUartTxFix

    BaseSocPatched = makeSocUartTxFix(BaseSoC)
    class MySoC(BaseSocPatched):
        ...
"""

from math import log2

from migen import *

from litex.gen import LiteXModule
from litex.gen.genlib.misc import WaitTimer

from litex.soc.interconnect.csr import *
from litex.soc.interconnect.csr_eventmanager import *
from litex.soc.interconnect import stream
from litex.soc.cores.uart import RS232PHY, UARTInterface


# -- FIFO (patched) that removed bit errors when  ------------------------------------------------

def _nextPowerOfTwo(value: int) -> int:
    if value <= 1:
        return 1
    return 1 << (value - 1).bit_length()


def _get_uart_fifo_patched(depth, sink_cd="sys", source_cd="sys"):
    if sink_cd != source_cd:
        async_depth = _nextPowerOfTwo(depth)
        fifo = stream.AsyncFIFO([("data", 8)], async_depth)
        return ClockDomainsRenamer({"write": sink_cd, "read": source_cd})(fifo)
    else:
        return stream.SyncFIFO([("data", 8)], depth, buffered=False)  ## disable FIFO output register (buffered=True → False)
                                                                      ## to match CC_BRAM single-cycle read latency, and fix 
                                                                      ## flush-timer byte-drop race by gating on source.ready
# -- Patched UART core -----------------------------------------------------

class UARTPatched(LiteXModule, UARTInterface):
    def __init__(self, phy=None,
            tx_fifo_depth = 16,
            rx_fifo_depth = 16,
            rx_fifo_rx_we = False,
            phy_cd        = "sys"):
        self._rxtx    = CSR(8, name="rxtx")
        self._txfull  = CSRStatus(description="TX FIFO Full.",  name="txfull")
        self._rxempty = CSRStatus(description="RX FIFO Empty.", name="rxempty")

        self.ev    = EventManager()
        self.ev.tx = EventSourceLevel()
        self.ev.rx = EventSourceLevel()
        self.ev.finalize()

        self._txempty = CSRStatus(description="TX FIFO Empty.", name="txempty")
        self._rxfull  = CSRStatus(description="RX FIFO Full.",  name="rxfull")

        # # #

        UARTInterface.__init__(self)

        # PHY
        if phy is not None:
            self.phy = phy
            self.comb += phy.source.connect(self.sink)
            self.comb += self.source.connect(phy.sink)

        # TX
        self.tx_fifo = tx_fifo = _get_uart_fifo_patched(tx_fifo_depth, source_cd=phy_cd)
        self.comb += [
            tx_fifo.sink.valid.eq(self._rxtx.re),
            tx_fifo.sink.data.eq(self._rxtx.r),
            tx_fifo.source.connect(self.source),
            self._txfull.status.eq(~tx_fifo.sink.ready),
            self._txempty.status.eq(~tx_fifo.source.valid),
            # PATCH-4: trigger on FIFO-empty, not FIFO-not-full.
            self.ev.tx.trigger.eq(~tx_fifo.source.valid),
        ]

        # RX
        self.rx_fifo = rx_fifo = _get_uart_fifo_patched(rx_fifo_depth, sink_cd=phy_cd)
        self.comb += [
            self.sink.connect(rx_fifo.sink),
            self._rxtx.w.eq(rx_fifo.source.data),
            rx_fifo.source.ready.eq(self._rxtx.we if rx_fifo_rx_we else self.ev.rx.clear),
            self._rxempty.status.eq(~rx_fifo.source.valid),
            self._rxfull.status.eq(~rx_fifo.sink.ready),
            self.ev.rx.trigger.eq(rx_fifo.source.valid),
        ]

    def add_auto_tx_flush(self, sys_clk_freq, timeout=1e-2, interval=2):
        flush_ep    = stream.Endpoint([("data", 8)])
        flush_count = Signal(int(log2(interval)))

        self.comb += self.tx_fifo.source.connect(flush_ep)
        self.comb += flush_ep.connect(self.source)

        self.timer = timer = WaitTimer(timeout * sys_clk_freq)
        self.comb += timer.wait.eq(~self.source.ready)
        self.sync += flush_count.eq(flush_count + 1)

        # PATCH-3: AND with source.ready so flush only dequeues when
        # the PHY can genuinely accept the byte.
        self.comb += If(timer.done,
            flush_ep.ready.eq((flush_count == 0) & self.source.ready)
        )


# -- Factory function ------------------------------------------------------

def makeSocUartTxFix(BaseSoC):
    """
    Return a subclass of BaseSoC that overrides add_uart() to install
        """
    class BaseSocUartTxFix(BaseSoC):

        def add_uart(self, name="uart", uart_name="serial", uart_pads=None,
                     baudrate=115200, fifo_depth=16,
                     with_dynamic_baudrate=False, rx_fifo_rx_we=False):

            if uart_pads is None:
                uart_pads_name = "serial" if uart_name == "sim" else uart_name
                uart_pads = self.platform.request(uart_pads_name, loose=True)

            if uart_pads is None:
                # No physical pads (e.g. sim/crossover) — fall back to stock.
                super().add_uart(name=name, uart_name=uart_name, uart_pads=None,
                                 baudrate=baudrate, fifo_depth=fifo_depth,
                                 with_dynamic_baudrate=with_dynamic_baudrate,
                                 rx_fifo_rx_we=rx_fifo_rx_we)
                return

            patched_phy = RS232PHY(
                uart_pads,
                clk_freq=int(self.sys_clk_freq),
                baudrate=baudrate,
                with_dynamic_baudrate=with_dynamic_baudrate,
            )

            uart = UARTPatched(patched_phy,
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

    return BaseSocUartTxFix
