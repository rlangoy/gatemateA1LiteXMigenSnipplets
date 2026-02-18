#!/usr/bin/env python3
"""
Host-side script to control the LED over UART Wishbone bridge.

Usage:
  1. Build and load the bitstream: python wishBoneBlink.py
  2. Start the LiteX server:       litex_server --uart --uart-port=/dev/ttyUSBX
  3. Run this script:               python ledControl.py

NB !
If you tries to access an andress that is not mapped to any periprihals, the WishBoneBus would hang waiting for an ack

"""
from litex import RemoteClient

wb = RemoteClient()
wb.open()

while(True):
   addr=0x40000400
   print(f" Write 0x01 to address 0x{addr:08x}  — turns the LED on - please verify")
   wb.write(addr, 0x1)

   # Read back to verify
   value = wb.read(addr)
   print(f"LED register = 0x{value:08x} (bit0={'ON' if value & 1 else 'OFF'})")

   input("Press Enter to continue...")
   print("Turn led off -- please verify")
   wb.write(addr, 0x0)

   # Read back to verify
   value = wb.read(addr)
   print(f"LED register = 0x{value:08x} (bit0={'ON' if value & 1 else 'OFF'})")

   input("Press Enter to continue...")

   ####

   addr=0x40000004
   print(f" Write 0x01 to address 0x{addr:08x}  — No device attetched noting should happen - please verify")
   wb.write(addr, 0x1)

   # Read back to verify
   value = wb.read(addr)
   print(f"Readback the  register = 0x{value:08x} (bit0={'ON' if value & 1 else 'OFF'})")

   input("Press Enter to continue...")
   print(f" Write 0x00 to address 0x{addr:08x}  — No device attetched noting should happen - please verify")
   wb.write(addr, 0x0)

wb.close()
