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

jetson_ip = get_jetson_ip()
print(f"Connecting to Jetson at {jetson_ip}...")

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(jetson_ip, username='om', password='gtaomp23', timeout=10)

# Restart sentinel.service cleanly
print("Restarting sentinel.service...")
stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S systemctl restart sentinel.service")
stdout.channel.recv_exit_status()

# Check status
stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service --no-pager | head -n 16")
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
print("Restart Complete!")
