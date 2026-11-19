from jetson_config import get_jetson_ssh
import time

ssh, ip = get_jetson_ssh()
ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")
time.sleep(1)

test_script = """
import spidev
import Jetson.GPIO as GPIO
import time

# Let's test with spidev controlling CS, but also test reading multiple times with loop
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000
spi.mode = 0

# Try reading registers 0x01 through 0x08, and 0x42
print("Dump registers:")
for reg in [0x01, 0x06, 0x07, 0x08, 0x12, 0x1D, 0x1E, 0x42]:
    val = spi.xfer2([reg & 0x7F, 0x00])[1]
    print(f"Reg 0x{reg:02X} = 0x{val:02X}")

spi.close()
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/dump_regs.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/dump_regs.py")
print(stdout.read().decode())
ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
ssh.close()

