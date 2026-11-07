import paramiko
import os
import time

JETSON_IP = "192.168.1.50"
JETSON_USER = "om"
JETSON_PASS = "gtaomp23"
REMOTE_BASE = "/home/om/disaster-sentinel-sih2026"
LOCAL_BASE = r"d:\Ai Disaster Management SIH 2026"

FILES_TO_SYNC = [
    ("firmware/node_fire/platformio.ini", f"{REMOTE_BASE}/firmware/node_fire/platformio.ini"),
    ("firmware/node_fire/src/config.h", f"{REMOTE_BASE}/firmware/node_fire/src/config.h"),
    ("firmware/node_fire/src/main.cpp", f"{REMOTE_BASE}/firmware/node_fire/src/main.cpp"),
    ("web/server.py", f"{REMOTE_BASE}/web/server.py"),
    ("web/templates/monitoring.html", f"{REMOTE_BASE}/web/templates/monitoring.html"),
    ("tools/serial_bridge.py", f"{REMOTE_BASE}/tools/serial_bridge.py"),
]

def run_ssh(ssh, cmd, sudo=False, timeout=180):
    print(f"\n[JETSON] >>> {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd, get_pty=True, timeout=timeout)
    if sudo:
        stdin.write(f"{JETSON_PASS}\n")
        stdin.flush()
    output = []
    for line in iter(stdout.readline, ""):
        print(line, end="", flush=True)
        output.append(line)
    code = stdout.channel.recv_exit_status()
    return code, "".join(output)

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    print(f"Connecting to Jetson at {JETSON_IP}...")
    ssh.connect(JETSON_IP, username=JETSON_USER, password=JETSON_PASS, timeout=15)
    sftp = ssh.open_sftp()

    print("\n--- Uploading updated files via SFTP ---")
    for rel_local, remote_path in FILES_TO_SYNC:
        full_local = os.path.join(LOCAL_BASE, rel_local.replace("/", "\\"))
        print(f"Uploading: {rel_local} -> {remote_path}")
        sftp.put(full_local, remote_path)
    sftp.close()
    print("Files successfully synced!")

    # Stop processes holding /dev/ttyUSB0
    run_ssh(ssh, "pkill -f serial_bridge.py || true")
    run_ssh(ssh, "echo gtaomp23 | sudo -S systemctl stop sentinel.service || true")
    time.sleep(1)

    # Compile and upload to /dev/ttyUSB0
    print("\n--- Compiling and Uploading Firmware to Fire Node (/dev/ttyUSB0) ---")
    upload_cmd = f"cd {REMOTE_BASE}/firmware/node_fire && /home/om/venv/bin/pio run -t upload --upload-port /dev/ttyUSB0"
    code, _ = run_ssh(ssh, upload_cmd, timeout=300)
    if code != 0:
        print(f"Upload failed with exit code {code}")
        ssh.close()
        return

    # Restart sentinel.service
    print("\n--- Restarting sentinel.service on Jetson ---")
    run_ssh(ssh, "echo gtaomp23 | sudo -S systemctl restart sentinel.service")
    time.sleep(6)

    # Print serial bridge output
    print("\n--- Live Serial Bridge Telemetry ---")
    run_ssh(ssh, "tail -n 35 /tmp/serial_bridge.log")

    # Check /api/nodes
    print("\n--- Verifying Active Node Telemetry (/api/nodes) ---")
    run_ssh(ssh, "curl -s http://127.0.0.1:5000/api/nodes | /home/om/venv/bin/python3 -m json.tool")

    ssh.close()
    print("\nAll done!")

if __name__ == "__main__":
    main()

