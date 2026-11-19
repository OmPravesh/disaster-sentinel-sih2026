from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()

script = """
import spidev

for speed in [100000, 500000, 1000000, 2000000]:
    for mode in [0, 1]:
        try:
            spi = spidev.SpiDev()
            spi.open(0, 0)
            spi.mode = mode
            spi.max_speed_hz = speed
            v = spi.xfer2([0x42 & 0x7F, 0x00])[1]
            op = spi.xfer2([0x01 & 0x7F, 0x00])[1]
            spi.close()
            print("Speed=" + str(speed) + " Mode=" + str(mode) + ": Version=0x" + hex(v) + " OpMode=0x" + hex(op))
        except Exception as e:
            print("Speed=" + str(speed) + " Mode=" + str(mode) + " Err: " + str(e))
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python -c '{script}'")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
ssh.close()
