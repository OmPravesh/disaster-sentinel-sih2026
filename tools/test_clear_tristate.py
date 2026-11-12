import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

script = r"""
import mmap, os, struct, subprocess

def clear_tristate(addr):
    fd = os.open("/dev/mem", os.O_RDWR | os.O_SYNC)
    mem = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE, offset=addr & ~0xfff)
    off = addr & 0xfff
    val = struct.unpack("<I", mem[off:off+4])[0]
    new_val = val & ~0x10  # clear TRISTATE bit (bit 4)
    print(f"0x{addr:08x}: 0x{val:08x} -> 0x{new_val:08x}")
    mem[off:off+4] = struct.pack("<I", new_val)
    readback = struct.unpack("<I", mem[off:off+4])[0]
    print(f"0x{addr:08x} readback: 0x{readback:08x}")
    mem.close()
    os.close(fd)

clear_tristate(0x02434088)  # Pin 12: soc_gpio41_ph7
clear_tristate(0x0243d020)  # Pin 16: spi3_cs1_py4

p1 = subprocess.check_output(["cat", "/sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups"]).decode()
lines = p1.splitlines()
for i, line in enumerate(lines):
    if "soc_gpio41_ph7" in line or "spi3_cs1_py4" in line:
        print("\n".join(lines[i:i+13]))
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/enable_pin12_16.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S python3 /tmp/enable_pin12_16.py")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
ssh.close()

