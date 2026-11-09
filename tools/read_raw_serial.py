import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23')

# Read directly from serial
script = """
import serial
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
for i in range(25):
    line = s.readline().decode('utf-8', 'replace').strip()
    if line:
        print(line)
s.close()
"""
ssh.exec_command("pkill -f serial_bridge.py")
time.sleep(0.5)
stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{script}\"")
print(stdout.read().decode('utf-8', 'replace'))

# Restart serial bridge
ssh.exec_command("nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py > /tmp/serial_bridge.log 2>&1 &")
ssh.close()

