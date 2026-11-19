from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
print(f"Connected to {ip}")

script = """
import spidev
spi = spidev.SpiDev()
spi.open(0, 0)
spi.max_speed_hz = 2000000

v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
irq = spi.xfer2([0x12 & 0x7F, 0x00])[1]
op = spi.xfer2([0x01 & 0x7F, 0x00])[1]

print(f"RegVersion (0x42): 0x{v:02X} (Expected: 0x12)")
print(f"RegIrqFlags (0x12): 0x{irq:02X}")
print(f"RegOpMode   (0x01): 0x{op:02X}")
spi.close()
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python -c '{script}'")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
ssh.close()
