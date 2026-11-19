from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")

test_script = """
import spidev, time

spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 500000
spi.mode = 0

reads = []
for _ in range(20):
    v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
    reads.append(hex(v))
    time.sleep(0.01)

print("Bus 0 Dev 0 Reads:", reads)
spi.close()
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_bus0.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/test_bus0.py")
print(stdout.read().decode())
ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
ssh.close()
