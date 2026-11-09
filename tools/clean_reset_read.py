import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

# Stop serial bridge
ssh.exec_command("pkill -f serial_bridge.py")
time.sleep(0.5)

# Use esptool to reset the chip into run mode cleanly
stdin, stdout, stderr = ssh.exec_command("/home/om/venv/bin/esptool.py --port /dev/ttyUSB0 run")
print("esptool run:")
print(stdout.read().decode('utf-8', 'replace'))

# Now open serial and read the first 30 lines
script = """
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
s.reset_input_buffer()
t0 = time.time()
while time.time() - t0 < 3.5:
    line = s.readline().decode('utf-8', 'replace').strip()
    if line:
        print(line)
s.close()
"""
stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{script}\"")
print("=== FRESH SERIAL OUTPUT ===")
print(stdout.read().decode('utf-8', 'replace'))

# Restart serial bridge
ssh.exec_command("nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py > /tmp/serial_bridge.log 2>&1 &")
ssh.close()

