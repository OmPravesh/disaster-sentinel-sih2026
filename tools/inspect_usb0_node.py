from jetson_config import get_jetson_ssh

ssh, ip = get_jetson_ssh()
print(f"Connected to {ip}")

# Stop serial bridge temporarily so we have exclusive serial access
ssh.exec_command("pkill -f serial_bridge.py")

script = """
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
# Reset ESP32:
s.setDTR(False)
s.setRTS(True)
time.sleep(0.1)
s.setRTS(False)
time.sleep(0.2)

t0 = time.time()
print('--- Reading /dev/ttyUSB0 ---')
while time.time() - t0 < 6:
    line = s.readline().decode('utf-8', errors='replace').strip()
    if line:
        print(line)
s.close()
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python -c \"{script}\"")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)

# Restart sentinel.service so serial bridge resumes
ssh.exec_command("echo gtaomp23 | sudo -S systemctl restart sentinel.service")
ssh.close()

