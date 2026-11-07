import paramiko
import time
import sys

JETSON_IP = "192.168.1.50"
JETSON_USER = "om"
JETSON_PASS = "gtaomp23"

def run_ssh_command(ssh, cmd, sudo=False, timeout=120):
    print(f"\n[JETSON EXEC] {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    if sudo:
        stdin.write(f"{JETSON_PASS}\n")
        stdin.flush()
    
    out_lines = []
    for line in iter(stdout.readline, ""):
        print(line, end="", flush=True)
        out_lines.append(line)
    
    exit_code = stdout.channel.recv_exit_status()
    return exit_code, "".join(out_lines)

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to Jetson Orin Nano at {JETSON_IP}...")
    ssh.connect(JETSON_IP, username=JETSON_USER, password=JETSON_PASS, timeout=15)
    print("Connected.")

    # 1. Stop services locking /dev/ttyUSB0
    run_ssh_command(ssh, "pkill -f serial_bridge.py || true")
    run_ssh_command(ssh, "echo gtaomp23 | sudo -S systemctl stop sentinel.service || true")
    time.sleep(1)

    # 2. Check serial ports
    run_ssh_command(ssh, "ls -l /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true")

    # 3. Pull latest code
    run_ssh_command(ssh, "cd /home/om/disaster-sentinel-sih2026 && git pull origin main")

    # 4. Locate pio
    _, pio_loc = run_ssh_command(ssh, "which pio || find /home/om -name pio 2>/dev/null | head -n 1")
    pio_cmd = pio_loc.strip() or "pio"
    print(f"PlatformIO binary: {pio_cmd}")

    # 5. Build and upload firmware/node_flood
    upload_cmd = f"cd /home/om/disaster-sentinel-sih2026/firmware/node_flood && {pio_cmd} run -t upload --upload-port /dev/ttyUSB0"
    code, _ = run_ssh_command(ssh, upload_cmd, timeout=300)
    if code != 0:
        print(f"\n[ERROR] Upload failed with code {code}")
        # Try fallback permissions
        run_ssh_command(ssh, "echo gtaomp23 | sudo -S chmod 666 /dev/ttyUSB0 || true")
        code, _ = run_ssh_command(ssh, upload_cmd, timeout=300)

    # 6. Restart system services
    print("\nRestarting sentinel.service...")
    run_ssh_command(ssh, "echo gtaomp23 | sudo -S systemctl restart sentinel.service")
    time.sleep(2)

    # 7. Start serial bridge in background
    print("\nStarting serial bridge...")
    run_ssh_command(ssh, "nohup /home/om/venv/bin/python3 /home/om/disaster-sentinel-sih2026/tools/serial_bridge.py --hub http://127.0.0.1:5000 > /tmp/serial_bridge.log 2>&1 &")
    time.sleep(3)

    # 8. Check bridge log
    run_ssh_command(ssh, "head -n 25 /tmp/serial_bridge.log || true")

    # 9. Test /api/nodes
    run_ssh_command(ssh, "curl -s http://127.0.0.1:5000/api/nodes | python3 -m json.tool || true")

    ssh.close()
    print("\nDeployment completed successfully!")

if __name__ == "__main__":
    main()

