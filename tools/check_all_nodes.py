import json
import urllib.request
from jetson_config import get_jetson_ssh

def inspect_system():
    print("==================================================")
    print("      DISASTER SENTINEL - NODE TRANSMISSION AUDIT")
    print("==================================================")
    
    # 1. Dashboard API
    try:
        req = urllib.request.urlopen("http://10.77.154.70:5000/api/nodes", timeout=3)
        data = json.loads(req.read().decode())
        nodes = data.get("nodes", {})
        for nid in ["FLD1", "SLD2", "FIR3", "POL4"]:
            n = nodes.get(nid, {})
            conn = n.get("connected", False)
            ago = n.get("last_seen_ago")
            status = n.get("status_display") or n.get("status")
            print(f"[{nid}] {n.get('name')}:")
            print(f"   Status: {'🟢 CONNECTED (' + str(round(ago, 1)) + 's ago)' if conn else '🔴 DISCONNECTED'}")
            print(f"   Risk / Condition: {status}")
            if conn:
                print(f"   Sensors: {n.get('sensors')}")
    except Exception as e:
        print(f"API Error: {e}")

    # 2. Hardware USB & Serial Inspection on Jetson
    ssh, ip = get_jetson_ssh()
    print(f"\n--- Jetson Hardware Interface ({ip}) ---")
    
    stdin, stdout, stderr = ssh.exec_command("lsusb")
    print("[USB Devices]:")
    print(stdout.read().decode().strip())
    
    stdin, stdout, stderr = ssh.exec_command("ls -l /dev/ttyUSB* /dev/ttyACM* 2>&1")
    print("\n[Serial Devices]:")
    print(stdout.read().decode().strip())

    stdin, stdout, stderr = ssh.exec_command("dmesg | tail -n 20")
    print("\n[Kernel dmesg tail]:")
    print(stdout.read().decode().strip())

    ssh.close()

if __name__ == "__main__":
    inspect_system()

