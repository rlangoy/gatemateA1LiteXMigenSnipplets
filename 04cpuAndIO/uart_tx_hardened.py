"""
RS232 timing-patched UART PHY for LiteX.

Improves first-byte TX robustness by enforcing explicit bit-time staging
and an optional pre-idle guard before the START bit. 
Drop-in replacement for the stock LiteX RS232PHY 
Usage: replace BaseSoc width SocUartTxHardened (by calling makeSocUartTxHardened) .
The difference between regular rs232 is that rhe transfer of data has an extra IDLE delay before Tx
Idle  Guard  Start   D0   D1   D2   D3   D4   D5   D6   D7   Stop  Idle
  1      1      0      x    x    x    x    x    x    x    x     1     1
        |<------------------ 10-bit frame --------------------->|
        
"""
from migen import *
from migen.genlib.record import Record
from migen.genlib.cdc import MultiReg

from litex.gen import LiteXModule
from litex.soc.interconnect import stream

RS232_IDLE  = 1
RS232_START = 0
RS232_STOP  = 1


def UARTPads():
    return Record([("tx", 1), ("rx", 1)])


class UARTInterface:
    def __init__(self):
        self.sink   = stream.Endpoint([("data", 8)])
        self.source = stream.Endpoint([("data", 8)])


class RS232ClkPhaseAccum(LiteXModule):
    """
    Same accumulator concept as LiteX:
      - tick from 32-bit phase accumulation using tuning_word.
      - RX starts at half-bit offset.
    """
    def __init__(self, tuning_word, mode="tx"):
        assert mode in ["tx", "rx"]
        self.enable = Signal()
        self.tick   = Signal()

        phase = Signal(32, reset_less=True)
        self.sync += Cat(phase, self.tick).eq(tuning_word if mode == "tx" else 2**31)
        self.sync += If(self.enable, Cat(phase, self.tick).eq(phase + tuning_word))


class RS232PHYTXPatched(LiteXModule):
    """
    Patched TX:
      - optional guard idle bit-times before first START after IDLE
      - explicit 10-bit frame serialization with stable one-tick-per-bit cadence

    This aims to reduce first-byte sampling margin problems with some USB-UART bridges.
    """
    def __init__(self, pads, tuning_word, guard_bits=1):
        self.sink = sink = stream.Endpoint([("data", 8)])

        pads.tx.reset = RS232_IDLE

        data        = Signal(8, reset_less=True)
        bit_index   = Signal(4, reset_less=True)   # 0..9 : start + 8 data + stop
        guard_count = Signal(4, reset_less=True)

        self.clk_phase_accum = clk = RS232ClkPhaseAccum(tuning_word, mode="tx")

        self.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            NextValue(bit_index, 0),
            NextValue(pads.tx, RS232_IDLE),
            If(sink.valid,
                NextValue(data, sink.data),
                If(guard_bits > 0,
                    NextValue(guard_count, guard_bits),
                    NextState("GUARD")
                ).Else(
                    NextState("RUN")
                )
            )
        )
        fsm.act("GUARD",
            clk.enable.eq(1),
            NextValue(pads.tx, RS232_IDLE),
            If(clk.tick,
                NextValue(guard_count, guard_count - 1),
                If(guard_count == 1,
                    NextState("RUN")
                )
            )
        )
        fsm.act("RUN",
            clk.enable.eq(1),
            If(clk.tick,
                # Serialize one bit each tick.
                If(bit_index == 0,
                    NextValue(pads.tx, RS232_START)
                ).Elif(bit_index <= 8,
                    NextValue(pads.tx, data[0]),
                    NextValue(data, Cat(data[1:], 0))
                ).Else(
                    NextValue(pads.tx, RS232_STOP)
                ),

                NextValue(bit_index, bit_index + 1),

                If(bit_index == 9,
                    sink.ready.eq(1),
                    NextState("IDLE")
                )
            )
        )


class RS232PHYRXCompatible(LiteXModule):
    """
    RX kept close to LiteX implementation for compatibility.
    """
    def __init__(self, pads, tuning_word):
        self.source = source = stream.Endpoint([("data", 8)])

        data  = Signal(8, reset_less=True)
        count = Signal(4, reset_less=True)

        self.clk_phase_accum = clk_phase_accum = RS232ClkPhaseAccum(tuning_word, mode="rx")

        rx   = Signal()
        rx_d = Signal()
        self.specials += MultiReg(pads.rx, rx)
        self.sync += rx_d.eq(rx)

        self.fsm = fsm = FSM(reset_state="IDLE")
        fsm.act("IDLE",
            NextValue(count, 0),
            If((rx == RS232_START) & (rx_d == RS232_IDLE),
                NextState("RUN")
            )
        )
        fsm.act("RUN",
            clk_phase_accum.enable.eq(1),
            If(clk_phase_accum.tick,
                NextValue(count, count + 1),
                NextValue(data, Cat(data[1:], rx)),
                If(count == (10 - 1),
                    source.valid.eq(rx == RS232_STOP),
                    source.data.eq(data),
                    NextState("IDLE")
                )
            )
        )


class RS232PHYPatched(LiteXModule):
    def __init__(self, pads, clk_freq, baudrate=115200, with_dynamic_baudrate=False, tx_guard_bits=1):
        tuning_word = int((baudrate/clk_freq)*2**32)
        if with_dynamic_baudrate:
            from litex.soc.interconnect.csr import CSRStorage
            self._tuning_word = CSRStorage(32, reset=tuning_word, name="tuning_word")
            tuning_word = self._tuning_word.storage

        self.tx = RS232PHYTXPatched(pads, tuning_word, guard_bits=tx_guard_bits)
        self.rx = RS232PHYRXCompatible(pads, tuning_word)
        self.sink, self.source = self.tx.sink, self.rx.source


# -------------------------------------------------
# Return the an extendex BaseSoC (BaseSocUartTxHardened) object.
# Class overrides add_uart() , so that the RS232PHYPatched is used instead of the stock RS232PHY.
# -------------------------------------------------
def makeSocUartTxHardened(BaseSoC):
    from litex.soc.cores.uart import UART

    class BaseSocUartTxHardened(BaseSoC):
        # ------------------------------------------------------------------
        # Override add_uart so BaseSoC uses RS232PHYPatched instead of the
        # default RS232PHY.  Called automatically by BaseSoC.__init__ via MRO.
        # Non-serial UART types (crossover, jtag_uart, …) are delegated to
        # the parent unchanged.
        # ------------------------------------------------------------------
        def add_uart(self, name="uart", uart_name="serial", uart_pads=None, baudrate=115200,
                     fifo_depth=16, with_dynamic_baudrate=False, rx_fifo_rx_we=False):

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

    return BaseSocUartTxHardened
