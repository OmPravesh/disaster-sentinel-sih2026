import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

# Temporarily stop serial bridge to read raw serial
ssh.exec_command("pkill -f serial_bridge.py")
time.sleep(0.5)

script = """
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
s.reset_input_buffer()
t0 = time.time()
while time.time() - t0 < 16:
    line = s.readline().decode('utf-8', 'replace').strip()
    if line:
        print(line)
s.close()
"""
stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{script}\"", timeout=25)
print(stdout.read().decode('utf-8', 'replace'))

# Restart serial bridge
ssh.exec_command("nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py > /tmp/serial_bridge.log 2>&1 &")
ssh.close()

