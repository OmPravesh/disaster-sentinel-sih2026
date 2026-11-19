import socket
import paramiko

def get_jetson_ip():
    candidate_ips = ['10.77.154.70', '192.168.1.50']
    for ip in candidate_ips:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.2)
            if s.connect_ex((ip, 22)) == 0:
                s.close()
                return ip
            s.close()
        except Exception:
            pass
    return '10.77.154.70'

def get_jetson_ssh(timeout=10):
    ip = get_jetson_ip()
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(ip, username='om', password='gtaomp23', timeout=timeout)
    return ssh, ip

