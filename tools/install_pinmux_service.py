import paramiko

JETSON_IP = "192.168.1.50"
JETSON_USER = "om"
JETSON_PASS = "gtaomp23"
REMOTE_DIR = "/home/om/disaster-sentinel-sih2026"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(JETSON_IP, username=JETSON_USER, password=JETSON_PASS, timeout=10)

sftp = ssh.open_sftp()
print("Uploading jetson/setup_gpio_pinmux.py...")
sftp.put("jetson/setup_gpio_pinmux.py", f"{REMOTE_DIR}/jetson/setup_gpio_pinmux.py")
sftp.close()

# Update sentinel.service safely to ensure ExecStartPre=+... is present
update_cmd = f"""
python3 - << 'EOF'
path = "/etc/systemd/system/sentinel.service"
with open(path, "r") as f:
    text = f.read()

line = "ExecStartPre=+/usr/bin/python3 {REMOTE_DIR}/jetson/setup_gpio_pinmux.py"
if line not in text:
    text = text.replace(
        "ExecStart=",
        line + "\\nExecStart=",
        1,
    )
    with open("/tmp/sentinel.service.new", "w") as f:
        f.write(text)
    print("UPDATED_SERVICE")
else:
    print("ALREADY_PRESENT")
EOF
"""

stdin, stdout, stderr = ssh.exec_command(update_cmd)
res = stdout.read().decode().strip()
print(res)
if "UPDATED_SERVICE" in res:
    cmds = [
        f"echo {JETSON_PASS} | sudo -S cp /tmp/sentinel.service.new /etc/systemd/system/sentinel.service",
        f"echo {JETSON_PASS} | sudo -S systemctl daemon-reload",
        f"echo {JETSON_PASS} | sudo -S systemctl restart sentinel.service",
    ]
    for c in cmds:
        stdin, stdout, stderr = ssh.exec_command(c)
        stdout.channel.recv_exit_status()
        err = stderr.read().decode().strip()
        if err and "[sudo]" not in err:
            print("ERR:", err)

# Verify service & pinconf
stdin, stdout, stderr = ssh.exec_command(
    f"echo {JETSON_PASS} | sudo -S cat /sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups | grep -A 3 -E 'soc_gpio41_ph7|spi3_cs1_py4'"
)
print("=== PINCONF CHECK ===")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("systemctl status sentinel.service --no-pager | head -n 18")
print("=== SERVICE STATUS ===")
print(stdout.read().decode())

ssh.close()
