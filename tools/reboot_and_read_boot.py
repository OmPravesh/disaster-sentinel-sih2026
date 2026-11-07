import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23')

print("Stopping serial_bridge to capture boot messages...")
ssh.exec_command('pkill -f serial_bridge.py')
time.sleep(1)

# Run a python script directly on the Jetson that resets ESP32 and reads boot
jetson_script = """
import serial, time
s = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
# Toggle DTR/RTS to reset ESP32
s.dtr = False
s.rts = True
time.sleep(0.1)
s.dtr = True
s.rts = False
time.sleep(0.1)
s.dtr = False
s.rts = False

t0 = time.time()
while time.time() - t0 < 12:
    line = s.readline().decode('utf-8', errors='replace').strip()
    if line:
        print(line)
s.close()
"""

stdin, stdout, stderr = ssh.exec_command(f"/home/om/venv/bin/python3 -c \"{jetson_script}\"")
print("\n--- ESP32 Boot Console ---")
boot_log = stdout.read().decode()
print(boot_log)

# Restart sentinel service to resume normal background bridge
ssh.exec_command('echo gtaomp23 | sudo -S systemctl restart sentinel.service')
ssh.close()
