import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

script = """
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=2)
# Trigger hardware reset on ESP32 via DTR/RTS
s.setDTR(False)
s.setRTS(True)
time.sleep(0.1)
s.setDTR(True)
s.setRTS(False)
time.sleep(0.1)
s.setDTR(False)

lines = []
t0 = time.time()
while time.time() - t0 < 4:
    line = s.readline().decode('utf-8', 'replace').strip()
    if line:
        lines.append(line)
s.close()
for l in lines:
    print(l)
"""

ssh.exec_command("pkill -f serial_bridge.py")
time.sleep(0.5)

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{script}\"")
boot_log = stdout.read().decode('utf-8', 'replace')
print("=== ESP32 LIVE BOOT LOG ===")
print(boot_log)

# Restart serial bridge
ssh.exec_command("nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py > /tmp/serial_bridge.log 2>&1 &")
ssh.close()

