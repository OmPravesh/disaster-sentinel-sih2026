import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

script = r"""
import mmap, os, struct, subprocess

# Dump pinconf for pg6, ph7, pi0, pi1, pi2, py0..py4, pz3..pz7
p1 = subprocess.check_output(["cat", "/sys/kernel/debug/pinctrl/2430000.pinmux/pinconf-groups"]).decode()
for line in p1.splitlines():
    if any(x in line for x in ['pg6', 'ph7', 'pi0', 'pi1', 'pi2', 'py0', 'py1', 'py2', 'py3', 'py4', 'pz3', 'pz4', 'pz5', 'pz6', 'pz7', 'pq5', 'pq6', 'pn1', 'pr5']):
        # print block
        idx = p1.splitlines().index(line)
        print("\n".join(p1.splitlines()[idx:idx+13]))
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/match_pinconf.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("echo gtaomp23 | sudo -S python3 /tmp/match_pinconf.py")
print(stdout.read().decode())
ssh.close()

