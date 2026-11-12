import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23', timeout=10)

stdin, stdout, stderr = ssh.exec_command('curl -s -X POST http://127.0.0.1:5000/api/actuators/buzzer/on')
print("Buzzer ON API Response:", stdout.read().decode('utf-8'))

time.sleep(2)

stdin, stdout, stderr = ssh.exec_command('curl -s http://127.0.0.1:5000/api/nodes')
resp = stdout.read().decode('utf-8')
print("Is buzzer_gpio18 still True in hub_state after 2 seconds?:", '"buzzer_gpio18": true' in resp)

ssh.close()
