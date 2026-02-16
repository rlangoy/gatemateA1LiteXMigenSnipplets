#!/usr/bin/env python3
"""
Simulation testbench to verify Wishbone address decoding.

Tests that the LED peripheral only responds at 0x40000000 and ignores
other addresses like 0x50000000.
"""

from migen import *
from litex.soc.interconnect import wishbone


class WishboneLed(Module):
    """Single-register Wishbone slave — bit 0 controls an active-low LED."""

    def __init__(self, led):
        self.bus = wishbone.Interface()
        led_reg = Signal()

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.cyc & self.bus.stb & ~self.bus.ack,
                self.bus.ack.eq(1),
                If(self.bus.we,
                    led_reg.eq(self.bus.dat_w[0]),
                ),
            ),
        ]

        self.comb += [
            self.bus.dat_r.eq(led_reg),
            led.eq(~led_reg),
        ]


class TestBench(Module):
    def __init__(self):
        self.led = Signal()
        self.master = wishbone.Interface()

        self.submodules.led_periph = led_periph = WishboneLed(self.led)

        self.submodules.decoder = wishbone.Decoder(
            self.master,
            [(lambda addr: addr[26:30] == 0b0100, led_periph.bus)],
        )


def wb_write(master, byte_addr, value):
    """Perform a Wishbone write cycle."""
    word_addr = byte_addr >> 2
    yield master.adr.eq(word_addr)
    yield master.dat_w.eq(value)
    yield master.we.eq(1)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    # Wait for ack (up to 10 cycles)
    for _ in range(10):
        ack = yield master.ack
        if ack:
            break
        yield
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield master.we.eq(0)
    yield


def wb_read(master, byte_addr):
    """Perform a Wishbone read cycle."""
    word_addr = byte_addr >> 2
    yield master.adr.eq(word_addr)
    yield master.we.eq(0)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    # Wait for ack (up to 10 cycles)
    for _ in range(10):
        ack = yield master.ack
        if ack:
            break
        yield
    value = yield master.dat_r
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield
    return value


def run_test(dut):
    led_val = yield dut.led
    print(f"Initial LED pin = {led_val} (expected 1, LED off)")

    # --- Test 1: Write 1 to correct address 0x40000000 ---
    print("\n--- Test 1: Write 1 to 0x40000000 (correct address) ---")
    yield from wb_write(dut.master, 0x40000000, 0x1)
    yield  # extra cycle for sync
    led_val = yield dut.led
    read_val = yield from wb_read(dut.master, 0x40000000)
    print(f"  Read back = 0x{read_val:08x}, LED pin = {led_val}")
    print(f"  PASS" if (read_val == 1 and led_val == 0) else f"  FAIL")

    # --- Test 2: Write 0 to correct address to reset ---
    print("\n--- Test 2: Write 0 to 0x40000000 (reset LED) ---")
    yield from wb_write(dut.master, 0x40000000, 0x0)
    yield
    led_val = yield dut.led
    read_val = yield from wb_read(dut.master, 0x40000000)
    print(f"  Read back = 0x{read_val:08x}, LED pin = {led_val}")
    print(f"  PASS" if (read_val == 0 and led_val == 1) else f"  FAIL")

    # --- Test 3: Write 1 to WRONG address 0x50000000 ---
    print("\n--- Test 3: Write 1 to 0x50000000 (wrong address, should be ignored) ---")
    yield from wb_write(dut.master, 0x50000000, 0x1)
    yield
    led_val = yield dut.led
    read_val = yield from wb_read(dut.master, 0x40000000)
    print(f"  Read back = 0x{read_val:08x}, LED pin = {led_val}")
    print(f"  PASS (write ignored)" if (read_val == 0 and led_val == 1) else f"  FAIL (write was NOT ignored!)")

    # --- Test 4: Write 1 to another wrong address 0x00000000 ---
    print("\n--- Test 4: Write 1 to 0x00000000 (wrong address, should be ignored) ---")
    yield from wb_write(dut.master, 0x00000000, 0x1)
    yield
    led_val = yield dut.led
    read_val = yield from wb_read(dut.master, 0x40000000)
    print(f"  Read back = 0x{read_val:08x}, LED pin = {led_val}")
    print(f"  PASS (write ignored)" if (read_val == 0 and led_val == 1) else f"  FAIL (write was NOT ignored!)")

    # --- Test 5: Confirm correct address still works after wrong writes ---
    print("\n--- Test 5: Write 1 to 0x40000000 again (should work) ---")
    yield from wb_write(dut.master, 0x40000000, 0x1)
    yield
    led_val = yield dut.led
    read_val = yield from wb_read(dut.master, 0x40000000)
    print(f"  Read back = 0x{read_val:08x}, LED pin = {led_val}")
    print(f"  PASS" if (read_val == 1 and led_val == 0) else f"  FAIL")


dut = TestBench()
run_simulation(dut, run_test(dut), vcd_name="test_address_decode.vcd")
