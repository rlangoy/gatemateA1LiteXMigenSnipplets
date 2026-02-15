# LiteX + PicoRV32 Setup on Ubuntu 24.04 LTS for GateMateA1-E

This document describes how to set up a complete LiteX development environment implementing a PicoRV32 soft CPU on the GateMateA1-E FPGA board.

Target OS: Ubuntu 24.04 LTS (Noble Numbat)
Target board vendor: Olimex
FPGA toolchain vendor: Cologne Chip

---

## 1. System Preparation

Update the system and install Python virtual environment support:

```bash
sudo apt update
sudo apt install python3.12-venv
```

Create and activate a virtual environment:

```bash
python3 -m venv py3env
echo 'source py3env/bin/activate' >> ~/.bashrc
source py3env/bin/activate
```

Install pip and git:

```bash
sudo apt install pip git
pip install --upgrade pip
```

---

## 2. Install LiteX

Create a working directory:

```bash
mkdir ~/LiteX && cd ~/LiteX
```

Download LiteX setup script:

```bash
wget https://raw.githubusercontent.com/enjoy-digital/litex/master/litex_setup.py
chmod +x litex_setup.py
```

Initialize and install LiteX:

```bash
./litex_setup.py --init --install
```

---

## 3. Install RISC-V Build Tools and PicoRV32 Support

Install compilation tools:

```bash
sudo apt install ninja-build gcc-riscv64-unknown-elf meson
```

Install PicoRV32 CPU package for LiteX:

```bash
pip3 install git+https://github.com/litex-hub/pythondata-cpu-picorv32.git
```

---

## 4. DirtyJTAG / Olimex USB Permissions

Add user to `dialout` group (log out and back in afterward):

```bash
sudo usermod -aG dialout student
```

Install required USB libraries:

```bash
sudo apt install libhidapi-libusb0 libftdi1-2 libusb-1.0-0 -y
```

Create udev rule for DirtyJTAG:

```bash
echo 'SUBSYSTEM=="usb", ATTR{idVendor}=="1209", ATTR{idProduct}=="c0ca", MODE="0666", GROUP="plugdev"' | sudo tee /etc/udev/rules.d/99-dirtyjtag.rules
```

Add user to `plugdev` and reload rules:

```bash
sudo usermod -aG plugdev student
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

## 5. Install CologneChip GateMate Toolchain (Legacy)

Download and extract:

```bash
cd
wget https://colognechip.com/downloads/cc-toolchain-linux.tar.gz
tar xzf ./cc-toolchain-linux.tar.gz && rm cc-toolchain-linux.tar.gz
```

Temporarily add tools to PATH:

```bash
export PATH=$PATH:/home/student/cc-toolchain-linux/bin/p_r:/home/student/cc-toolchain-linux/bin/openFPGALoader:/home/student/cc-toolchain-linux/bin/yosys
```

Make PATH permanent:

```bash
echo 'export PATH=$PATH:/home/student/cc-toolchain-linux/bin/p_r:/home/student/cc-toolchain-linux/bin/openFPGALoader:/home/student/cc-toolchain-linux/bin/yosys' >> ~/.bashrc
source ~/.bashrc
```

---
#### Note 
The new toolchain oss-cad-suite (https://github.com/YosysHQ/oss-cad-suite-build) as of2026-02-11 11:43:26 +0100 ,does not work width LiteX (/litex/build/colognechip/colognechip.py needs patching (replace it with litexPatch/colognechip.py))

## 6. Environment Ready

At this point you have:

- Python virtual environment
- LiteX framework
- PicoRV32 CPU support
- RISC-V GCC toolchain
- DirtyJTAG USB access
- CologneChip GateMate synthesis & programming tools

You are now ready to build LiteX designs targeting the GateMateA1-E.

---

## Optional Verification

```bash
litex_setup --help
riscv64-unknown-elf-gcc --version
yosys -V
openFPGALoader --version
```

---

## Done

You now have a complete LiteX + PicoRV32 development environment for GateMateA1-E on Ubuntu 24.04.
