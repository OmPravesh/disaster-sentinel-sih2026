import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

script = r"""
import os, subprocess, re
os.environ["JETSON_MODEL_NAME"] = "JETSON_ORIN_NANO"
from Jetson.GPIO import gpio_pin_data

_, _, pin_dict = gpio_pin_data.get_data()
board_pins = pin_dict['BOARD']

p1 = subprocess.check_output(["cat", "/sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups"]).decode()
p2 = subprocess.check_output(["cat", "/sys/kernel/debug/pinctrl/c300000.pinmux/pinconf-groups"]).decode()
all_conf = p1 + "\n" + p2

blocks = {}
cur = None
for line in all_conf.splitlines():
    m = re.match(r'^\d+\s+\(([^)]+)\):', line)
    if m:
        cur = m.group(1)
        blocks[cur] = {}
    elif cur and '=' in line:
        k, v = line.strip().split('=', 1)
        blocks[cur][k] = v

print("--- BOARD PINS MAPPING ---")
for pin in sorted(board_pins.keys()):
    info = board_pins[pin]
    print(f"Pin {pin:2d}: {vars(info)}")

print("\n--- PINCONF GROUPS MATCHING HEADER OR GPIO-MODE=1 ---")
for k, v in sorted(blocks.items()):
    if v.get('gpio-mode') == '1' or any(x in k for x in ['ph7','ph6','py4','py3','py2','py1','py0','pg6','pr5','pr4','pq5','pq6','pn1','pcc4','pac6','pz3','pz4','pz5','pz6','pz7','pi0','pi1','pi2','ph0','pee2']):
        print(f"{k:28s} | gpio-mode={v.get('gpio-mode')} tristate={v.get('tristate')} in={v.get('enable-input')} od={v.get('open-drain')} pull={v.get('pull')}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/scan_pinconf.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S python3 /tmp/scan_pinconf.py")
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print("ERR:", err)
ssh.close()
