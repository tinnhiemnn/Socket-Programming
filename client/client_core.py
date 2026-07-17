import socket
import sys

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.control_socket = None

    def connect_control_channel(self):
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            self.control_socket.connect((self.server_ip, self.server_port))
            print(f"[*] Connected to FTP Server {self.server_ip}:{self.server_port}")
            
            response = self.control_socket.recv(1024).decode('utf-8')
            print(response)
        except Exception as e:
            print(f"[!] Cannot connect to Server: {e}")
            sys.exit(1)
    
    def send_command(self, cmd_string):
        try:
            if not cmd_string.endswith("\r\n"):
                cmd_string += "\r\n"

            self.control_socket.send(cmd_string.encode('utf-8'))
            response = self.control_socket.recv(1024).decode('utf-8')
            return response
        except Exception as e:
            return f"[!] Error control channel: {e}"