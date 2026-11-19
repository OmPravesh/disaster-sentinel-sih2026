import time
import json
import urllib.request
from jetson_config import get_jetson_ssh

def check_nodes():
    print("--- 1. Checking HTTP /api/nodes on Dashboard ---")
    try:
        req = urllib.request.urlopen("http://10.77.154.70:5000/api/nodes", timeout=3)
        data = json.loads(req.read().decode())
        nodes = data.get("nodes", {})
        for node_id, info in nodes.items():
            status = info.get("status_display") or info.get("status")
            connected = info.get("connected")
            last_seen = info.get("last_seen_ago")
            print(f"[{node_id}] {info.get('name')}: Connected={connected}, Status={status}, Last seen={last_seen}s ago")
            if connected:
                print(f"       Sensors: {info.get('sensors')}")
    except Exception as e:
        print(f"API query failed: {e}")

    print("\n--- 2. Checking Jetson Serial Ports & Bridges ---")
    ssh, ip = get_jetson_ssh()
    cmd = """
python3 -c "
import subprocess

p = subprocess.Popen(['journalctl', '-u', 'sentinel.service', '-n', '50', '--no-pager'], stdout=subprocess.PIPE, text=True)
out, _ = p.communicate()
for line in out.splitlines():
    if any(k in line.lower() for k in ['bridge', 'serial', 'fld', 'sld', 'fir', 'pol', 'received', 'packet']):
        print(line)
"
"""
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print(stdout.read().decode())

    print("\n--- 3. Checking Active Processes under sentinel.service ---")
    stdin, stdout, stderr = ssh.exec_command("ps aux | grep -E 'python|serial|main.py' | grep -v grep")
    print(stdout.read().decode())

    ssh.close()

if __name__ == "__main__":
    check_nodes()

