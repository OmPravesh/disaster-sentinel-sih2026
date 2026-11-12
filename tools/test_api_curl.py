import time
import paramiko

time.sleep(3)
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

# Test GET /api/actuators
run("curl -s http://127.0.0.1:5000/api/actuators")

# Test POST buzzer ON
run("curl -s -X POST http://127.0.0.1:5000/api/actuators/buzzer/on")

# Test GET /api/actuators again
run("curl -s http://127.0.0.1:5000/api/actuators")

# Check tail of /tmp/sentinel_server.log
run("tail -n 15 /tmp/sentinel_server.log")

ssh.close()
