from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
ssh.exec_command("echo gtaomp23 | sudo -S systemctl stop sentinel.service")

test_script = """
import spidev

for bus, dev in [(0, 0), (0, 1), (1, 0), (1, 1)]:
    try:
        spi = spidev.SpiDev()
        spi.open(bus, dev)
        spi.max_speed_hz = 500000
        spi.mode = 0
        v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
        spi.close()
        print(f"Bus={bus} Dev={dev} -> RegVersion (0x42): 0x{v:02X}")
    except Exception as e:
        print(f"Bus={bus} Dev={dev} -> Error: {e}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_all_spi.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/python /tmp/test_all_spi.py")
print(stdout.read().decode())
ssh.exec_command("echo gtaomp23 | sudo -S systemctl start sentinel.service")
ssh.close()
