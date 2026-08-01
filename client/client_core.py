import socket
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from client.client_data import ClientDataHandler
from client.cli_formatter import print_status

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.control_socket = None
        self.client_data = ClientDataHandler()
        self.transfer_type = 'I'
        self.data_mode = 'PASV'
        self.active_udp_socket = None

    def connect_control_channel(self):
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            self.control_socket.connect((self.server_ip, self.server_port))
            print_status(f"Connected to FTP Server {self.server_ip}:{self.server_port}", "INFO")
            
            response = self.control_socket.recv(1024).decode('utf-8')
            print_status(response.strip(), "NET")
        except Exception as e:
            print_status(f"Cannot connect to Server: {e}", "ERROR")
            sys.exit(1)
    
    def send_command(self, cmd_string):
        try:
            if not cmd_string.endswith("\r\n"):
                cmd_string += "\r\n"

            self.control_socket.send(cmd_string.encode('utf-8'))
            response = self.control_socket.recv(1024).decode('utf-8')
            return response
        except Exception as e:
            return f"Error control channel: {e}"

    def set_type(self, type_str):
        res = self.send_command(f"TYPE {type_str}")
        if "200" in res:
            self.transfer_type = type_str.upper()
        return res

    def enable_passive_mode(self):
        res = self.send_command("PASV")
        if "227" in res:
            # Bóc tách chuỗi (127,0,0,1,p1,p2)
            start = res.find("(") + 1
            end = res.find(")")
            parts = res[start:end].split(",")
            ip = ".".join(parts[:4])
            port = int(parts[4]) * 256 + int(parts[5])
            self.data_mode = 'PASV'
            return (ip, port)
        raise Exception("Failed to enter Passive Mode.")

    def get_local_ip(self):
        try:
            temp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            temp_sock.connect((self.server_ip, self.server_port))
            local_ip = temp_sock.getsockname()[0]
            temp_sock.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def enable_active_mode(self):
        client_ip = self.get_local_ip()
        
        if self.active_udp_socket:
            self.active_udp_socket.close()
        self.active_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.active_udp_socket.bind((client_ip, 0))  
        
        client_port = self.active_udp_socket.getsockname()[1]
        
        ip_parts = client_ip.split('.')
        p1 = client_port // 256
        p2 = client_port % 256
        
        port_cmd = f"PORT {ip_parts[0]},{ip_parts[1]},{ip_parts[2]},{ip_parts[3]},{p1},{p2}"
        response = self.send_command(port_cmd)
        
        if "200" in response:
            self.data_mode = 'PORT'
        return response

    def download_file(self, filename, save_local_path): 
        udp_sock = None
        target_addr = None

        try:
            if self.data_mode == 'PASV':
                target_addr = self.enable_passive_mode()
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else: 
                if not self.active_udp_socket:
                    self.enable_active_mode()
                udp_sock = self.active_udp_socket

            res_150 = self.send_command(f"RETR {filename}")
            if "150" not in res_150:
                if self.data_mode == 'PASV' and udp_sock:
                    udp_sock.close()
                return res_150

            if self.data_mode == 'PASV':
                udp_sock.sendto(b'PING', target_addr)
                self.client_data.handle_download(udp_sock, save_local_path, self.transfer_type)
                udp_sock.close()
            else:
                self.client_data.handle_download(udp_sock, save_local_path, self.transfer_type)
                udp_sock.close()
                self.active_udp_socket = None 

            res_226 = self.control_socket.recv(1024).decode('utf-8')
            return res_226

        except Exception as e:
            if self.data_mode == 'PASV' and udp_sock:
                udp_sock.close()
            return f"Download failed: {e}"
        
    def upload_file(self, local_filepath, remote_filename): 
        udp_sock = None
        target_addr = None

        try:
            if self.data_mode == 'PASV':
                target_addr = self.enable_passive_mode()
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else:
                if not self.active_udp_socket:
                    self.enable_active_mode()
                udp_sock = self.active_udp_socket

            res_150 = self.send_command(f"STOR {remote_filename}")
            if "150" not in res_150:
                if self.data_mode == 'PASV' and udp_sock:
                    udp_sock.close()
                return res_150

            if self.data_mode == 'PASV':
                self.client_data.handle_upload(udp_sock, target_addr, local_filepath, self.transfer_type)
                udp_sock.close()
            else:
                udp_sock.settimeout(3.0)
                _, server_udp_addr = udp_sock.recvfrom(1024)
                self.client_data.handle_upload(udp_sock, server_udp_addr, local_filepath, self.transfer_type)
                udp_sock.close()
                self.active_udp_socket = None 

            res_226 = self.control_socket.recv(1024).decode('utf-8')
            return res_226

        except Exception as e:
            if self.data_mode == 'PASV' and udp_sock:
                udp_sock.close()
            return f"Upload failed: {e}"

    def list_directory(self, cmd_string):
        udp_sock = None
        target_addr = None

        try:
            if self.data_mode == 'PASV':
                target_addr = self.enable_passive_mode()
                udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            else: 
                if not self.active_udp_socket:
                    self.enable_active_mode()
                udp_sock = self.active_udp_socket

            res_150 = self.send_command(cmd_string)
            if "150" not in res_150:
                if self.data_mode == 'PASV' and udp_sock:
                    udp_sock.close()
                return res_150

            if self.data_mode == 'PASV':
                udp_sock.sendto(b'PING', target_addr)
                raw_bytes = self.client_data.rdt_channel.receive_data_rdt(udp_sock)
                udp_sock.close()
            else:
                raw_bytes = self.client_data.rdt_channel.receive_data_rdt(udp_sock)
                udp_sock.close()
                self.active_udp_socket = None  

            res_226 = self.control_socket.recv(1024).decode('utf-8')
            
            dir_text = raw_bytes.decode('utf-8', errors='replace')
            print("\n--- Directory Listing ---")
            print(dir_text if dir_text.strip() else "(Directory is empty)")
            print("-------------------------\n")

            return res_226

        except Exception as e:
            if self.data_mode == 'PASV' and udp_sock:
                udp_sock.close()
            return f"LIST failed: {e}"
    