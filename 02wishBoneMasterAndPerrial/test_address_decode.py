#!/usr/bin/env python3
"""
Simulation testbench to verify Wishbone address decoding.

Tests that:
- LED peripheral only updates at 0x40000000
- Writes to other addresses (0x50000000, 0x20000000, 0x00000000) are ACKed
  but do not affect the LED register
- The bus never hangs on any address
"""

from migen import *
from litex.soc.interconnect import wishbone

ADDR_LED_UPPER = 0b0100


class WishboneLed(Module):
    """Wishbone slave with built-in address decoding."""

    def __init__(self, led):
        self.bus = wishbone.Interface(data_width=32, adr_width=30)
        led_reg = Signal()
        addr_match = Signal()

        self.comb += addr_match.eq(
            (self.bus.adr[26:30] == ADDR_LED_UPPER) &
            (self.bus.adr[0:26] == 0)
        )

        self.sync += [
            self.bus.ack.eq(0),
            If(self.bus.cyc & self.bus.stb & ~self.bus.ack,
                self.bus.ack.eq(1),
                If(self.bus.we & addr_match,
                    led_reg.eq(self.bus.dat_w[0]),
                ),
            ),
        ]

        self.comb += [
            If(addr_match,
                self.bus.dat_r.eq(led_reg),
            ).Else(
                self.bus.dat_r.eq(0),
            ),
            led.eq(~led_reg),
        ]


class TestBench(Module):
    def __init__(self):
        self.led = Signal()
        self.master = wishbone.Interface(data_width=32, adr_width=30)
        self.submodules.led_periph = WishboneLed(self.led)
        self.comb += self.master.connect(self.led_periph.bus)


def wb_write(master, byte_addr, value):
    """Perform a Wishbone write cycle. Returns True if ACKed within 10 cycles."""
    yield master.adr.eq(byte_addr >> 2)
    yield master.dat_w.eq(value)
    yield master.we.eq(1)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    acked = False
    for _ in range(10):
        if (yield master.ack):
            acked = True
            break
        yield
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield master.we.eq(0)
    yield
    return acked


def wb_read(master, byte_addr):
    """Perform a Wishbone read cycle. Returns (value, acked)."""
    yield master.adr.eq(byte_addr >> 2)
    yield master.we.eq(0)
    yield master.sel.eq(0xF)
    yield master.cyc.eq(1)
    yield master.stb.eq(1)
    yield
    acked = False
    for _ in range(10):
        if (yield master.ack):
            acked = True
            break
        yield
    value = yield master.dat_r
    yield master.cyc.eq(0)
    yield master.stb.eq(0)
    yield
    return value, acked


def run_test(dut):
    passed = 0
    failed = 0

    led_val = yield dut.led
    print(f"Initial LED pin = {led_val} (expected 1, LED off)")

    # --- Test 1: Write 1 to correct address 0x40000000 ---
    print("\n--- Test 1: Write 1 to 0x40000000 (correct address) ---")
    acked = yield from wb_write(dut.master, 0x40000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 1 and led_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 2: Write 0 to correct address to reset ---
    print("\n--- Test 2: Write 0 to 0x40000000 (reset LED) ---")
    acked = yield from wb_write(dut.master, 0x40000000, 0x0)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 3: Write 1 to WRONG address 0x50000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 3: Write 1 to 0x50000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x50000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 4: Write 1 to WRONG address 0x20000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 4: Write 1 to 0x20000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x20000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 5: Write 1 to WRONG address 0x00000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 5: Write 1 to 0x00000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x00000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 6: Confirm correct address still works after wrong writes ---
    print("\n--- Test 6: Write 1 to 0x40000000 again (should still work) ---")
    acked = yield from wb_write(dut.master, 0x40000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000000)
    ok = read_val == 1 and led_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 7: Read from WRONG address (should ACK with data=0) ---
    print("\n--- Test 7: Read from 0x20000000 (wrong addr, should ACK with 0) ---")
    read_val, acked = yield from wb_read(dut.master, 0x20000000)
    ok = read_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)



    # --- Test 8: Read from adjacent address 0x40000004 (next word, should not match) ---
    print("\n--- Test 8: Read from 0x40000004 (adjacent word, should return 0) ---")
    acked = yield from wb_write(dut.master, 0x40000004, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, 0x40000004)
    ok = read_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")


dut = TestBench()
run_simulation(dut, run_test(dut), vcd_name="test_address_decode.vcd")
