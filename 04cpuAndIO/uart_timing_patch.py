#!/usr/bin/env python3
#
# Local UART timing patch for LiteX-based projects.
# Goal: improve first-byte TX robustness by enforcing explicit bit-time staging
# and optional pre-idle guard before START bit.

from migen import *
from migen.genlib.record import Record
from migen.genlib.cdc import MultiReg

from litex.gen import LiteXModule
from litex.soc.interconnect import stream

# Reuse RS232 conventions from LiteX.
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
