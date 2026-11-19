from jetson_config import get_jetson_ssh
import time

ssh, ip = get_jetson_ssh()
print(f"Connected to {ip}")

# Stop sentinel.service temporarily so SPI bus is not contended
print("Stopping sentinel.service for exclusive SPI test...")
stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")
stdout.channel.recv_exit_status()

test_script = """import spidev
import time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 1000000
spi.mode = 0

print("Reading 10 consecutive Version register (0x42) values:")
versions = []
for i in range(10):
    v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
    versions.append(hex(v))
    time.sleep(0.05)
print("Versions:", versions)

op = spi.xfer2([0x01 & 0x7F, 0x00])[1]
print("RegOpMode (0x01):", hex(op))

spi.xfer2([0x01 | 0x80, 0x00])
time.sleep(0.01)
sleep_op = spi.xfer2([0x01 & 0x7F, 0x00])[1]
print("After Sleep write:", hex(sleep_op))

spi.xfer2([0x01 | 0x80, 0x81])
time.sleep(0.01)
standby_op = spi.xfer2([0x01 & 0x7F, 0x00])[1]
print("After Standby write:", hex(standby_op))

v2 = spi.xfer2([0x42 & 0x7F, 0x00])[1]
print("Version after mode switch:", hex(v2))

irq = spi.xfer2([0x12 & 0x7F, 0x00])[1]
print("RegIrqFlags (0x12):", hex(irq))

spi.close()
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_lora_spi.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/test_lora_spi.py")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

# Restart sentinel.service
print("Restarting sentinel.service...")
stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
stdout.channel.recv_exit_status()
ssh.close()
