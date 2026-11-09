import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

# Restart sentinel.service cleanly
stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl restart sentinel.service")
stdout.channel.recv_exit_status()

# Check status
stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service | head -n 12")
print("=== Restarted sentinel.service ===")
print(stdout.read().decode('utf-8', 'replace'))

# Check USB devices
stdin, stdout, stderr = ssh.exec_command("lsusb")
print("=== USB Devices connected to Jetson ===")
print(stdout.read().decode('utf-8', 'replace'))

# Check /dev/ttyUSB* or /dev/ttyACM*
stdin, stdout, stderr = ssh.exec_command("ls -l /dev/ttyUSB* /dev/ttyACM* 2>&1")
print("=== Serial Ports ===")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()

