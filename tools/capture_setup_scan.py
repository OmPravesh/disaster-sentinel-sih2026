import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

# Stop serial bridge
ssh.exec_command("pkill -f serial_bridge.py")
time.sleep(0.5)

script = """
import serial, time

s = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)

# Hardware reset ESP32: RTS pulls EN low
s.setDTR(False)
s.setRTS(True)
time.sleep(0.15)
s.setRTS(False)

lines = []
t0 = time.time()
cur_line = ""
while time.time() - t0 < 3.0:
    chunk = s.read(128).decode('utf-8', 'replace')
    if chunk:
        cur_line += chunk
        if '\\n' in cur_line:
            parts = cur_line.split('\\n')
            for p in parts[:-1]:
                p = p.strip()
                if p:
                    print(p)
            cur_line = parts[-1]
s.close()
"""
stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{script}\"")
print("=== SETUP SCAN CAPTURE ===")
print(stdout.read().decode('utf-8', 'replace'))

# Restart serial bridge
ssh.exec_command("nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py > /tmp/serial_bridge.log 2>&1 &")
ssh.close()

