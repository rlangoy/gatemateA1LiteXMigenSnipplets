#!/usr/bin/env python3
"""Copy uart.py to the LiteX soc/cores directory."""

import litex
import shutil
from pathlib import Path

script_dir = Path(__file__).parent
src = script_dir / "uart.py"
dst = Path(litex.__file__).parent.parent / "litex" / "soc" / "cores" / "uart.py"

print(f"Copying {src} -> {dst}")
shutil.copy2(src, dst)
print("Done.")
