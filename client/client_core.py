import socket
import sys
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from client.client_data import RDTDataChannel

class Client:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.control_socket = None
        self.rdt_data_channel = RDTDataChannel()
        self.transfer_type = 'I'

    def connect_control_channel(self):
        try:
            self.control_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            
            self.control_socket.connect((self.server_ip, self.server_port))
            print(f"[*] Connected to FTP Server {self.server_ip}:{self.server_port}")
            
            response = self.control_socket.recv(1024).decode('utf-8')
            print(f"Server: {response.strip()}")
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

    def set_type(self, type_str):
        res = self.send_command(f"TYPE {type_str}")
        if "200" in res:
            self.transfer_type = type_str.upper()
        return res

    def pasv(self):
        """Bật Passive Mode và trả về IP + Port UDP của Server"""
        res = self.send_command("PASV")
        if "227" in res:
            # Bóc tách chuỗi (127,0,0,1,p1,p2)
            start = res.find("(") + 1
            end = res.find(")")
            parts = res[start:end].split(",")
            ip = ".".join(parts[:4])
            port = int(parts[4]) * 256 + int(parts[5])
            return (ip, port)
        raise Exception("Không thể bật Passive Mode!")

    def download_file(self, filename, save_local_path): # CHƯA CÓ CHẾ ĐỘ ACTIVE
        # 1. Bật Passive Mode lấy Port UDP Server
        server_udp_addr = self.pasv()
        
        # 2. Tạo Socket UDP Client
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 3. Gửi lệnh RETR qua TCP
        res_150 = self.send_command(f"RETR {filename}")
        if "150" not in res_150:
            udp_sock.close()
            return res_150
            
        # 4. Gửi 1 gói tin mồi (Ping) sang UDP Server để Server biết IP/Port Client
        udp_sock.sendto(b'PING', server_udp_addr)
        
        # 5. Client đóng vai UDP Receiver hứng dữ liệu RDT
        raw_bytes = self.rdt_data_channel.receive_data_rdt(udp_sock)
        self.rdt_data_channel.write_file_payload(save_local_path, raw_bytes, self.transfer_type)
        udp_sock.close()
        
        # 6. Đón phản hồi 226 Transfer complete qua TCP[cite: 2]
        res_226 = self.control_socket.recv(1024).decode('utf-8')
        return res_226

    def upload_file(self, local_filepath, remote_filename): # CHƯA CÓ CHẾ ĐỘ ACTIVE
        # 1. Đọc file cục bộ
        payload_bytes = self.rdt_data_channel.read_file_payload(local_filepath, self.transfer_type)
        
        # 2. Bật Passive Mode lấy Port UDP Server
        server_udp_addr = self.pasv()
        udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        # 3. Gửi lệnh STOR qua TCP
        res_150 = self.send_command(f"STOR {remote_filename}")
        if "150" not in res_150:
            udp_sock.close()
            return res_150
            
        # 4. Client đóng vai UDP Sender đẩy dữ liệu RDT
        self.rdt_data_channel.send_data_rdt(udp_sock, server_udp_addr, payload_bytes)
        udp_sock.close()
        
        # 5. Đón phản hồi 226 Transfer complete qua TCP[cite: 2]
        res_226 = self.control_socket.recv(1024).decode('utf-8')
        return res_226