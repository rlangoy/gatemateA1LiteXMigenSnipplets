#!/usr/bin/env python3
"""
Simulation testbench to verify LedPeripheral from uartWishBoneCrsLed.py.

Tests that:
- LED peripheral only updates at 0x40000400 (led CSR control register)
- Writes to other addresses (0x50000000, 0x20000000, 0x00000000) are ACKed
  but do not affect the LED register
- The bus never hangs on any address
"""

from migen import *
from litex.soc.interconnect import wishbone
from litex.soc.interconnect import csr_bus
from litex.soc.interconnect.wishbone import Wishbone2CSR
from uartWishBoneCrsLed import LedPeripheral, Top

# Replicate the CSR address map from uartWishBoneCrsLed.py Top class.
# Address = csr_base + csr_map[peripheral] × csr_paging
CSR_PAGING    = 0x400                          # csr_paging from Top.__init__
CSR_BASE      = Top.mem_map["csr"]             # 0x40000000
ADDR_LED_CTRL = CSR_BASE + Top.csr_map["led"] * CSR_PAGING  # 0x40000400


class TestBench(Module):
    # Mirror the address maps from uartWishBoneCrsLed.py Top class
    mem_map = Top.mem_map   # {"csr": 0x40000000, ...}
    csr_map = Top.csr_map   # {"ctrl": 0, "led": 1}

    def __init__(self):
        self.led = Signal()
        self.master = wishbone.Interface(data_width=32, adr_width=30)

        # DUT: LedPeripheral from uartWishBoneCrsLed.py
        self.submodules.led_periph = LedPeripheral(self.led)

        # 32-bit CSR bus (matches default csr_data_width=32 in uartWishBoneCrsLed.py)
        csr_if = csr_bus.Interface(data_width=32)

        # CSR bank at the slot defined by csr_map["led"], with matching paging
        # CSRBank takes paging in bytes; divides by 4 internally for word alignment
        self.submodules.csr_bank = csr_bus.CSRBank(
            self.led_periph.get_csrs(),
            address=self.csr_map["led"],
            paging=CSR_PAGING,
            bus=csr_if,
        )

        # Wishbone → CSR bridge
        self.submodules.wb2csr = Wishbone2CSR(
            bus_wishbone=self.master,
            bus_csr=csr_if,
        )


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

    # --- Test 1: Write 1 to correct address 0x40000400 ---
    print(f"\n--- Test 1: Write 1 to 0x{ADDR_LED_CTRL:08x} (correct address) ---")
    acked = yield from wb_write(dut.master, ADDR_LED_CTRL, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
    ok = read_val == 1 and led_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 2: Write 0 to correct address to reset ---
    print(f"\n--- Test 2: Write 0 to 0x{ADDR_LED_CTRL:08x} (reset LED) ---")
    acked = yield from wb_write(dut.master, ADDR_LED_CTRL, 0x0)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 3: Write 1 to WRONG address 0x50000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 3: Write 1 to 0x50000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x50000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 4: Write 1 to WRONG address 0x20000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 4: Write 1 to 0x20000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x20000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 5: Write 1 to WRONG address 0x00000000 (must ACK, must NOT change LED) ---
    print("\n--- Test 5: Write 1 to 0x00000000 (wrong addr, should ACK but not change LED) ---")
    acked = yield from wb_write(dut.master, 0x00000000, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
    ok = read_val == 0 and led_val == 1 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    # --- Test 6: Confirm correct address still works after wrong writes ---
    print(f"\n--- Test 6: Write 1 to 0x{ADDR_LED_CTRL:08x} again (should still work) ---")
    acked = yield from wb_write(dut.master, ADDR_LED_CTRL, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL)
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

    # --- Test 8: Write/read adjacent address 0x40000404 (next word, should not match) ---
    print(f"\n--- Test 8: Read from 0x{ADDR_LED_CTRL+4:08x} (adjacent word, should return 0) ---")
    acked = yield from wb_write(dut.master, ADDR_LED_CTRL + 4, 0x1)
    yield
    led_val = yield dut.led
    read_val, _ = yield from wb_read(dut.master, ADDR_LED_CTRL + 4)
    ok = read_val == 0 and acked
    print(f"  ACKed={acked}, Read back=0x{read_val:08x}, LED pin={led_val}")
    print(f"  {'PASS' if ok else 'FAIL'}")
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed")


dut = TestBench()
run_simulation(dut, run_test(dut), vcd_name="test_address_decode.vcd")
