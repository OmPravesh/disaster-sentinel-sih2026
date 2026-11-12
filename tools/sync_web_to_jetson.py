import paramiko

JETSON_IP = '192.168.1.50'
JETSON_USER = 'om'
JETSON_PASS = 'gtaomp23'
REMOTE_DIR = '/home/om/disaster-sentinel-sih2026'

print(f"Connecting to Jetson at {JETSON_IP}...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(JETSON_IP, username=JETSON_USER, password=JETSON_PASS, timeout=10)
sftp = ssh.open_sftp()

files_to_sync = [
    ("web/server.py", f"{REMOTE_DIR}/web/server.py"),
    ("web/templates/dashboard.html", f"{REMOTE_DIR}/web/templates/dashboard.html"),
    ("web/templates/hardware.html", f"{REMOTE_DIR}/web/templates/hardware.html"),
    ("jetson/alerts/buzzer_strobe.py", f"{REMOTE_DIR}/jetson/alerts/buzzer_strobe.py"),
]

for local_path, remote_path in files_to_sync:
    print(f"Uploading {local_path} -> {remote_path}...")
    sftp.put(local_path, remote_path)

sftp.close()
print("All files uploaded successfully!")

print("\nRestarting sentinel.service...")
stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl restart sentinel.service")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service | head -n 14")
print("\n=== sentinel.service Status ===")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()
print("Sync & Restart Done!")
