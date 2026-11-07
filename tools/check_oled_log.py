import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.50', username='om', password='gtaomp23')

stdin, stdout, stderr = ssh.exec_command('grep -i oled /tmp/serial_bridge.log')
print("OLED lines in serial_bridge.log:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('head -n 25 /tmp/serial_bridge.log')
print("\nBoot header lines:")
print(stdout.read().decode())

ssh.close()

