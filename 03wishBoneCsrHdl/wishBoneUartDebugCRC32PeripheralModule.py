from litex import RemoteClient

wb = RemoteClient()
wb.open()

print("Testing the CRC32Peripherial module 0x40000800 ---")
# Feed bytes into the CRC32 accumulator (only lower 8 bits are used)

print("\n--- Test 1: write byte 0x31 at 0x40000800 ---\n")
wb.write(0x40000800, 0x31)   # byte '1'
value = wb.read(0x40000800)
expectedValue=0x83DCEFB7
print(f"Readback Result value x{value:08x} " )
if(value!=expectedValue):
    print(f"Failed ! Expected value x{expectedValue:08x} \n")
else:
    print(" - Value correct\n")

print("\n--- Test 2: write byte 0x32 at 0x40000800 ---\n")
wb.write(0x40000800, 0x32)   # byte '2'
value = wb.read(0x40000800)
expectedValue=0x4F5344CD
print(f"Readback Result value x{value:08x} " )
if(value!=expectedValue):
    print(f"Failed ! Expected value x{expectedValue:08x} \n")
else:
    print(" - Value correct\n")

print("\n--- Test 2: write byte 0x33 at 0x40000800 ---\n")
wb.write(0x40000800, 0x33)   # byte '3'
value = wb.read(0x40000800)
expectedValue=0x884863D2
print(f"Readback Result value x{value:08x} " )
if(value!=expectedValue):
    print(f"Failed ! Expected value x{expectedValue:08x} \n")
else:
    print(" - Value correct\n")



wb.close()