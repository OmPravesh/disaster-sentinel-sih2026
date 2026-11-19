import paramiko
import socket

def get_jetson_ip():
    candidate_ips = ['10.77.154.70', '192.168.1.50']
    for ip in candidate_ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            if s.connect_ex((ip, 22)) == 0:
                s.close()
                return ip
            s.close()
        except Exception:
            pass
    return '10.77.154.70'

JETSON_IP = get_jetson_ip()
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

stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service --no-pager | head -n 16")
print("\n=== sentinel.service Status ===")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()
print("Sync & Restart Done!")
