#!/usr/bin/env python3
"""
Host-side script to control the LED over UART Wishbone bridge.

Usage:
  1. Build and load the bitstream: python wishBoneBlink.py
  2. Start the LiteX server:       litex_server --uart --uart-port=/dev/ttyUSBX
  3. Run this script:               python ledControl.py
"""
from litex import RemoteClient

wb = RemoteClient()
wb.open()

# Write 0x01 to address 0x40000000 — turns the LED on
wb.write(0x40000000, 0x1)

# Read back to verify
value = wb.read(0x40000000)
print(f"LED register = 0x{value:08x} (bit0={'ON' if value & 1 else 'OFF'})")

wb.close()
