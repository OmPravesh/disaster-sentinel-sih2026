import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("192.168.1.50", username="om", password="gtaomp23")

def run(cmd):
    print(">>> " + cmd)
    stdin, stdout, stderr = ssh.exec_command(cmd)
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(out)
    if err:
        print("[ERR] " + err)

# Check journal logs for sentinel.service
run("journalctl -u sentinel.service -n 50 --no-pager")

ssh.close()
