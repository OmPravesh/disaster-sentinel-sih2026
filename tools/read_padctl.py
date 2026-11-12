import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

script = r"""
import mmap, os, struct

def read_regs(base, count=32):
    fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
    mem = mmap.mmap(fd, 0x1000, mmap.MAP_SHARED, mmap.PROT_READ, offset=base & ~0xfff)
    off = base & 0xfff
    for i in range(count):
        addr = base + i*4
        val = struct.unpack("<I", mem[off+i*4 : off+i*4+4])[0]
        print(f"0x{addr:08x}: 0x{val:08x}  bin={val:016b}")
    mem.close()
    os.close(fd)

print("=== 0x02434060 .. 0x024340c0 (PH7 / PG6 area) ===")
read_regs(0x02434060, 24)

print("=== 0x0243d000 .. 0x0243d060 (SPI3 PY area) ===")
read_regs(0x0243d000, 24)
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/read_padctl.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S python3 /tmp/read_padctl.py")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
ssh.close()

