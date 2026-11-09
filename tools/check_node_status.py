import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command("tail -n 40 /tmp/serial_bridge.log")
output = stdout.read().decode('utf-8', 'replace')
print("--- Recent /tmp/serial_bridge.log output ---")
print(output)

stdin, stdout, stderr = ssh.exec_command("curl -s http://127.0.0.1:5000/api/nodes | /home/om/venv/bin/python3 -c 'import sys, json; data=json.load(sys.stdin); print(json.dumps(data.get(\"nodes\", {}).get(\"SLD2\", {}), indent=2))'")
print("\n--- Dashboard API State for SLD2 ---")
print(stdout.read().decode('utf-8', 'replace'))

ssh.close()

