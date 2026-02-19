#!/usr/bin/env python3
"""
Simulation testbench for CRC32Peripheral.

The Migen simulator uses Icarus Verilog and cannot simulate VHDL black-boxes,
so this testbench uses a pure-Migen CRC32 step (MigenCRC32Step) that mirrors
hdl/crc.vhdl bit-for-bit.  All other logic is identical to CRC32Peripheral.

Single register (crc32_data @ 0x40000800):
  write [7:0]  → feeds one byte into the CRC32 accumulator
  read  [31:0] → running CRC32 checksum (inverted accumulator)

Accumulator resets to 0xFFFFFFFF on system reset.

Results are validated against the generated-Python reference in tbLib/crcLib.py.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from migen import *
from litex.soc.interconnect import wishbone, csr_bus
from litex.soc.interconnect.wishbone import Wishbone2CSR
from litex.soc.interconnect.csr import AutoCSR, CSR
from tbLib.crcLib import crc32 as crc32_ref
from wishBoneCrsCrc32Vhdl import Top

# ---------------------------------------------------------------------------
# Address constants
# ---------------------------------------------------------------------------
CSR_PAGING = 0x400
CSR_BASE   = Top.mem_map["csr"]                      # 0x40000000
CRC32_SLOT = Top.csr_map["crc32"]                    # 2
ADDR_DATA  = CSR_BASE + CRC32_SLOT * CSR_PAGING      # 0x40000800


# ---------------------------------------------------------------------------
# Pure-Migen CRC32 combinatorial step — bit-for-bit mirror of hdl/crc.vhdl
# ---------------------------------------------------------------------------
class MigenCRC32Step(Module):
    """Combinatorial: crcIn(32) × data(8) → crcOut(32)."""
    def __init__(self, crc_in, data, crc_out):
        i = crc_in
        d = data
        o = crc_out
        self.comb += [
            o[0] .eq(i[2]  ^ i[8]  ^ d[2]),
            o[1] .eq(i[0]  ^ i[3]  ^ i[9]  ^ d[0] ^ d[3]),
            o[2] .eq(i[0]  ^ i[1]  ^ i[4]  ^ i[10] ^ d[0] ^ d[1] ^ d[4]),
            o[3] .eq(i[1]  ^ i[2]  ^ i[5]  ^ i[11] ^ d[1] ^ d[2] ^ d[5]),
            o[4] .eq(i[0]  ^ i[2]  ^ i[3]  ^ i[6]  ^ i[12] ^ d[0] ^ d[2] ^ d[3] ^ d[6]),
            o[5] .eq(i[1]  ^ i[3]  ^ i[4]  ^ i[7]  ^ i[13] ^ d[1] ^ d[3] ^ d[4] ^ d[7]),
            o[6] .eq(i[4]  ^ i[5]  ^ i[14] ^ d[4] ^ d[5]),
            o[7] .eq(i[0]  ^ i[5]  ^ i[6]  ^ i[15] ^ d[0] ^ d[5] ^ d[6]),
            o[8] .eq(i[1]  ^ i[6]  ^ i[7]  ^ i[16] ^ d[1] ^ d[6] ^ d[7]),
            o[9] .eq(i[7]  ^ i[17] ^ d[7]),
            o[10].eq(i[2]  ^ i[18] ^ d[2]),
            o[11].eq(i[3]  ^ i[19] ^ d[3]),
            o[12].eq(i[0]  ^ i[4]  ^ i[20] ^ d[0] ^ d[4]),
            o[13].eq(i[0]  ^ i[1]  ^ i[5]  ^ i[21] ^ d[0] ^ d[1] ^ d[5]),
            o[14].eq(i[1]  ^ i[2]  ^ i[6]  ^ i[22] ^ d[1] ^ d[2] ^ d[6]),
            o[15].eq(i[2]  ^ i[3]  ^ i[7]  ^ i[23] ^ d[2] ^ d[3] ^ d[7]),
            o[16].eq(i[0]  ^ i[2]  ^ i[3]  ^ i[4]  ^ i[24] ^ d[0] ^ d[2] ^ d[3] ^ d[4]),
            o[17].eq(i[0]  ^ i[1]  ^ i[3]  ^ i[4]  ^ i[5]  ^ i[25] ^ d[0] ^ d[1] ^ d[3] ^ d[4] ^ d[5]),
            o[18].eq(i[0]  ^ i[1]  ^ i[2]  ^ i[4]  ^ i[5]  ^ i[6]  ^ i[26] ^ d[0] ^ d[1] ^ d[2] ^ d[4] ^ d[5] ^ d[6]),
            o[19].eq(i[1]  ^ i[2]  ^ i[3]  ^ i[5]  ^ i[6]  ^ i[7]  ^ i[27] ^ d[1] ^ d[2] ^ d[3] ^ d[5] ^ d[6] ^ d[7]),
            o[20].eq(i[3]  ^ i[4]  ^ i[6]  ^ i[7]  ^ i[28] ^ d[3] ^ d[4] ^ d[6] ^ d[7]),
            o[21].eq(i[2]  ^ i[4]  ^ i[5]  ^ i[7]  ^ i[29] ^ d[2] ^ d[4] ^ d[5] ^ d[7]),
            o[22].eq(i[2]  ^ i[3]  ^ i[5]  ^ i[6]  ^ i[30] ^ d[2] ^ d[3] ^ d[5] ^ d[6]),
            o[23].eq(i[3]  ^ i[4]  ^ i[6]  ^ i[7]  ^ i[31] ^ d[3] ^ d[4] ^ d[6] ^ d[7]),
            o[24].eq(i[0]  ^ i[2]  ^ i[4]  ^ i[5]  ^ i[7]  ^ d[0] ^ d[2] ^ d[4] ^ d[5] ^ d[7]),
            o[25].eq(i[0]  ^ i[1]  ^ i[2]  ^ i[3]  ^ i[5]  ^ i[6]  ^ d[0] ^ d[1] ^ d[2] ^ d[3] ^ d[5] ^ d[6]),
            o[26].eq(i[0]  ^ i[1]  ^ i[2]  ^ i[3]  ^ i[4]  ^ i[6]  ^ i[7]  ^ d[0] ^ d[1] ^ d[2] ^ d[3] ^ d[4] ^ d[6] ^ d[7]),
            o[27].eq(i[1]  ^ i[3]  ^ i[4]  ^ i[5]  ^ i[7]  ^ d[1] ^ d[3] ^ d[4] ^ d[5] ^ d[7]),
            o[28].eq(i[0]  ^ i[4]  ^ i[5]  ^ i[6]  ^ d[0] ^ d[4] ^ d[5] ^ d[6]),
            o[29].eq(i[0]  ^ i[1]  ^ i[5]  ^ i[6]  ^ i[7]  ^ d[0] ^ d[1] ^ d[5] ^ d[6] ^ d[7]),
            o[30].eq(i[0]  ^ i[1]  ^ i[6]  ^ i[7]  ^ d[0] ^ d[1] ^ d[6] ^ d[7]),
            o[31].eq(i[1]  ^ i[7]  ^ d[1] ^ d[7]),
        ]


# ---------------------------------------------------------------------------
# Simulation peripheral — identical logic to CRC32Peripheral, no VHDL Instance
# ---------------------------------------------------------------------------
class SimCRC32Peripheral(Module, AutoCSR):
    """Drop-in simulation stand-in for CRC32Peripheral (no VHDL Instance).

    CSRBank signal conventions (from csr_bus.py CSRBank.do_finalize):
      c.r  = data FROM host (bus dat_w → c.r)   — input byte
      c.w  = data TO host   (c.w → bus dat_r)   — checksum output
      c.re = fires when host WRITES
      c.we = fires when host READS
    """
    def __init__(self):
        self.data      = CSR(32, name="data")
        self.sim_reset = Signal()  # simulation-only reset (mirrors system reset behaviour)

        crc_in  = Signal(32, reset=0xFFFFFFFF)
        crc_out = Signal(32)
        out_buf = Signal(32, reset=0xFFFFFFFF)

        self.submodules.crc_step = MigenCRC32Step(crc_in, self.data.r[0:8], crc_out)

        self.sync += [
            If(self.sim_reset,
                crc_in.eq(0xFFFFFFFF),
                out_buf.eq(0xFFFFFFFF),
            ).Elif(self.data.re,        # c.re fires when host writes
                crc_in.eq(crc_out),
                out_buf.eq(crc_out),
            )
        ]

        # c.w is what the host reads — expose inverted accumulator
        self.comb += self.data.w.eq(~out_buf)


# ---------------------------------------------------------------------------
# TestBench — wires up: SimCRC32Peripheral → CSRBank → Wishbone2CSR → master
# ---------------------------------------------------------------------------
class TestBench(Module):
    def __init__(self):
        self.master = wishbone.Interface(data_width=32, adr_width=30)

        self.submodules.dut = SimCRC32Peripheral()

        csr_if = csr_bus.Interface(data_width=32)

        self.submodules.csr_bank = csr_bus.CSRBank(
            self.dut.get_csrs(),
            address=CRC32_SLOT,
            paging=CSR_PAGING,
            bus=csr_if,
        )

        self.submodules.wb2csr = Wishbone2CSR(
            bus_wishbone=self.master,
            bus_csr=csr_if,
        )


# ---------------------------------------------------------------------------
# Wishbone helpers
# ---------------------------------------------------------------------------
def wb_write(master, byte_addr, value):
    yield master.adr.eq(byte_addr >> 2)
    yield master.dat_w.eq(value)
    yield master.we.eq(1)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    for _ in range(10):
        if (yield master.ack):
            break
        yield
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield master.we.eq(0)
    yield


def wb_read(master, byte_addr):
    yield master.adr.eq(byte_addr >> 2)
    yield master.we.eq(0)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    for _ in range(10):
        if (yield master.ack):
            break
        yield
    value = yield master.dat_r
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield
    return value


def sys_reset(dut, cycles=2):
    """Drive sim_reset for `cycles` clock cycles, mirroring system reset."""
    yield dut.dut.sim_reset.eq(1)
    for _ in range(cycles):
        yield
    yield dut.dut.sim_reset.eq(0)
    yield


# ---------------------------------------------------------------------------
# Reference helper
# ---------------------------------------------------------------------------
def ref_checksum(data_bytes):
    crc = 0xFFFFFFFF
    for b in data_bytes:
        crc = crc32_ref(crc, b)
    return (~crc) & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Test sequence
# ---------------------------------------------------------------------------
def run_test(dut):
    passed = 0
    failed = 0

    def check(label, got, expected):
        nonlocal passed, failed
        ok = got == expected
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}: got 0x{got:08x}, expected 0x{expected:08x}")
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # ------------------------------------------------------------------
    # Test 1: Initial checksum at power-on
    # out_buf resets to 0xFFFFFFFF → checksum = ~0xFFFFFFFF = 0x00000000
    # ------------------------------------------------------------------
    print("\n--- Test 1: Initial checksum (power-on, no writes) ---")
    val = yield from wb_read(dut.master, ADDR_DATA)
    check("checksum at power-on", val, 0x00000000)

    # ------------------------------------------------------------------
    # Test 2: Single byte 0x31 ('1') — read and write share same address
    # ------------------------------------------------------------------
    print("\n--- Test 2: Single byte 0x31 at 0x40000800 ---")
    yield from wb_write(dut.master, ADDR_DATA, 0x31 & 0xFF)
    yield                                          # let sync latch out_buf
    val = yield from wb_read(dut.master, ADDR_DATA)
    check("checksum after 0x31", val, ref_checksum([0x31]))

    # ------------------------------------------------------------------
    # Test 3: Known CRC32 vector — "123456789" = 0xCBF43926
    # Reset accumulator via system reset, then feed all 9 bytes.
    # Each byte is masked to 8 bits before writing.
    # ------------------------------------------------------------------    
    print("\n--- Test 3: add Single byte 0x26 at 0x40000800 ---")
    yield from wb_write(dut.master, ADDR_DATA, 0x26)
    yield                                          # let sync latch out_buf
    val = yield from wb_read(dut.master, ADDR_DATA)
    check("checksum after 0x26", val, 0x558990b0)

    # ------------------------------------------------------------------
    # Test 4: System reset clears accumulator back to initial state
    # ------------------------------------------------------------------
    print("\n--- Test 4: System reset clears accumulator ---")
    yield from sys_reset(dut)
    val = yield from wb_read(dut.master, ADDR_DATA)
    check("checksum after system reset", val, 0x00000000)

    # ------------------------------------------------------------------
    # Test 5: Byte-by-byte accumulation matches crcLib.py at every step
    # ------------------------------------------------------------------
    print("\n--- Test 5: Byte-by-byte match against crcLib.py (0xDEADBEEF) ---")
    yield from sys_reset(dut)
    ref_crc = 0xFFFFFFFF
    for byte in b"\xDE\xAD\xBE\xEF":
        yield from wb_write(dut.master, ADDR_DATA, byte & 0xFF)
        yield
        ref_crc = crc32_ref(ref_crc, byte)
        val = yield from wb_read(dut.master, ADDR_DATA)
        check(f"  after byte 0x{byte:02x}", val, (~ref_crc) & 0xFFFFFFFF)

    # ------------------------------------------------------------------
    # Test 6: Upper bits [31:8] in a write must not affect the CRC.
    # Write 0xDEADBE31 and verify the result equals writing 0x31 alone.
    # ------------------------------------------------------------------
    print("\n--- Test 6: Upper bits [31:8] ignored — 0xDEADBE31 treated as 0x31 ---")
    yield from sys_reset(dut)
    yield from wb_write(dut.master, ADDR_DATA, 0xDEADBE31)   # upper 24 bits set
    yield
    val = yield from wb_read(dut.master, ADDR_DATA)
    check("0xDEADBE31 masked to 0x31", val, ref_checksum([0x31]))

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")
    if failed:
        raise SystemExit(1)


dut = TestBench()
run_simulation(dut, run_test(dut), vcd_name="test_crc32_peripheral.vcd")
