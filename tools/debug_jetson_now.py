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

run("grep -E 'POST|ACTUATOR|GPIO|ERROR|Exception' /tmp/sentinel_server.log | tail -n 50")
run("curl -s http://127.0.0.1:5000/api/actuators")
run("ls -la /tmp/*pin12* /tmp/*hold* 2>/dev/null || true")
run("cat /tmp/hold_pin12_high.py 2>/dev/null || true")

ssh.close()

