#!/usr/bin/env python3
"""
Jetson Orin Nano (JetPack 6 / L4T R36.x) 40-Pin Header Pinmux Output Enabler.

On JetPack 6, NVIDIA's default pinmux leaves unused 40-pin header pins with
TRISTATE=1 in the Tegra234 PADCTL registers, blocking Jetson.GPIO / libgpiod
outputs at 0V even when the kernel GPIO line reports `out hi`.

This script clears the TRISTATE bit (bit 4) on the actuator output pins:
  - Physical Pin 12 (soc_gpio41_ph7 / PH.07): 0x02434088  -> Buzzer
  - Physical Pin 16 (spi3_cs1_py4   / PY.04): 0x0243d020  -> Warning Strobe Relay

Must run with root privileges (e.g., via systemd ExecStartPre=+...).
"""

import mmap
import os
import struct

PADCTL_ACTUATOR_PINS = {
    "Pin 12 (PH.07 / Buzzer)": 0x02434088,
    "Pin 16 (PY.04 / Strobe)": 0x0243d020,
}

TRISTATE_BIT = 1 << 4  # 0x10


def enable_gpio_output_pads() -> None:
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    try:
        for label, addr in PADCTL_ACTUATOR_PINS.items():
            page_base = addr & ~0xFFF
            offset = addr & 0xFFF
            mem = mmap.mmap(
                fd,
                0x1000,
                mmap.MAP_SHARED,
                mmap.PROT_READ | mmap.PROT_WRITE,
                offset=page_base,
            )
            try:
                val = struct.unpack("<I", mem[offset : offset + 4])[0]
                if val & TRISTATE_BIT:
                    new_val = val & ~TRISTATE_BIT
                    mem[offset : offset + 4] = struct.pack("<I", new_val)
                    print(f"[PINMUX] {label} @ 0x{addr:08x}: cleared TRISTATE (0x{val:08x} -> 0x{new_val:08x})")
                else:
                    print(f"[PINMUX] {label} @ 0x{addr:08x}: already enabled (0x{val:08x})")
            finally:
                mem.close()
    finally:
        os.close(fd)


if __name__ == "__main__":
    enable_gpio_output_pads()
