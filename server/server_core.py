import sys
import os
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.protocol import *
from server.server_data import ServerDataHandler, log_event
SERVER_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'storage', 'server_root'))

class ClientHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        self.is_authenticated = False
        self.username = None
        self.is_running = True
        self.current_dir = SERVER_ROOT

        self.data_mode = "PASV"
        self.transfer_type = 'I' 
        self.data_handler = ServerDataHandler(client_address)
        self.pasv_udp_socket = None
        self.client_udp_addr = None

    def send_response(self, response_str): 
        """Send an FTP response code to the client."""
        try: 
            self.client_socket.sendall(response_str.encode('utf-8'))
            log_event(self.client_address, "*", response_str.strip())
        except Exception as e:
            log_event(self.client_address, "!", f"Failed to send response: {e}")

    def run(self):
        log_event(self.client_address, "+", "Client connected successfully.")
        self.send_response(REPLY_220)

        while self.is_running:
            try:
                data = self.client_socket.recv(1024).decode('utf-8')
                if not data:
                    break

                data = data.strip()
                parts = data.split(' ', 1)
                cmd = parts[0].upper()
                args = parts[1] if len(parts) > 1 else ""

                log_event(self.client_address, ">", f"{cmd} {args}".strip())
                self.process_command(cmd, args)

            except Exception as e:
                log_event(self.client_address, "-", f"Connection lost: {e}")
                break

        self.client_socket.close()
        log_event(self.client_address, "-", "Connection closed.")

    def process_command(self, cmd, args):
        """Validate and process FTP commands."""
        if cmd == "USER":
            self.expected_user = "admin"
            self.expected_pass = "123456"

            if args == self.expected_user:
                self.username = args
                self.send_response(REPLY_331) 
            else:
                self.send_response(REPLY_530) 
            return

        elif cmd == "PASS":
            if self.username and args == self.expected_pass:
                self.is_authenticated = True
                self.send_response(REPLY_230)
            else:
                self.send_response(REPLY_530)
            return

        elif cmd == "QUIT":
            self.send_response(REPLY_221)
            self.is_running = False
            return

        if not self.is_authenticated:
            self.send_response(REPLY_530)
            return

        if cmd == "TYPE":
            if args.upper() in ['A', 'I']:
                self.transfer_type = args.upper()
                self.send_response(REPLY_200)
            else:
                self.send_response(REPLY_500)

        elif cmd == "PASV":
            self.data_mode = "PASV"
            try:
                if self.pasv_udp_socket:
                    self.pasv_udp_socket.close()
                
                self.pasv_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.pasv_udp_socket.bind(('0.0.0.0', 0))
                
                _, assigned_port = self.pasv_udp_socket.getsockname()
                
                server_ip = self.client_socket.getsockname()[0]
                ip_parts = server_ip.replace('.', ',')
                p1 = assigned_port // 256
                p2 = assigned_port % 256

                log_event(self.client_address, "~", f"Passive UDP Socket bound on port {assigned_port}")
                # Gửi chuỗi 227 chứa IP và Port về cho Client
                self.send_response(REPLY_227.format(ip_parts, p1, p2))
            except Exception as e:
                self.send_response(REPLY_425)

        elif cmd == "PORT":
            self.data_mode = "PORT"
            try:
                parts = args.split(',')
                ip = '.'.join(parts[:4])
                port = int(parts[4]) * 256 + int(parts[5])
                
                # Lưu lại IP và Port của Client để dùng cho lệnh RETR/STOR
                self.client_udp_addr = (ip, port)
                log_event(self.client_address, "~", f"Active mode target configured -> {self.client_udp_addr[0]}:{self.client_udp_addr[1]}")
                self.send_response(REPLY_200)
            except:
                self.send_response(REPLY_501)

        elif cmd == "RETR": 
            filepath = os.path.abspath(os.path.join(self.current_dir, args))
            
            if not filepath.startswith(SERVER_ROOT) or not os.path.isfile(filepath):
                self.send_response(REPLY_550) # Báo lỗi nếu đòi lấy file ngoài luồng hoặc file không tồn tại
                return
            
            self.send_response(REPLY_150) 
            
            # 2. BAO BỌC TRONG TRY-EXCEPT để chống sập server
            try:
                if self.data_mode == "PASV" and self.pasv_udp_socket:
                    self.pasv_udp_socket.settimeout(3.0)
                    _, client_udp_addr = self.pasv_udp_socket.recvfrom(1024)
                    
                    self.data_handler.handle_download(self.pasv_udp_socket, client_udp_addr, filepath, self.transfer_type)
                    
                    self.pasv_udp_socket.close()
                    self.pasv_udp_socket = None
                    self.send_response(REPLY_226) 

                elif self.data_mode == "PORT" and getattr(self, 'client_udp_addr', None):
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.data_handler.handle_download(temp_socket, self.client_udp_addr, filepath, self.transfer_type)
                    
                    temp_socket.close()
                    self.send_response(REPLY_226) 
                
                else:
                    self.send_response(REPLY_425) 

            except socket.timeout:
                log_event(self.client_address, "!", f"RETR Timeout waiting for client.")
                self.send_response(REPLY_426)
            except Exception as e:
                log_event(self.client_address, "!", f"RETR Error: {e}")
                self.send_response(REPLY_426)

        elif cmd == "STOR": 
            save_filepath = os.path.abspath(os.path.join(self.current_dir, args))
            
            if not save_filepath.startswith(SERVER_ROOT):
                self.send_response(REPLY_550) 
                return
            
            self.send_response(REPLY_150) 
            
            # 2. BAO BỌC TRONG TRY-EXCEPT để bắt lỗi
            try:
                if self.data_mode == "PASV" and self.pasv_udp_socket:
                    self.pasv_udp_socket.settimeout(5.0) 
                    
                    self.data_handler.handle_upload(self.pasv_udp_socket, save_filepath, self.transfer_type)
                    
                    self.pasv_udp_socket.close()
                    self.pasv_udp_socket = None
                    self.send_response(REPLY_226) 

                elif self.data_mode == "PORT" and getattr(self, 'client_udp_addr', None):
                    # Chế độ PORT: Tự mở socket mới, bind đại 1 port rồi lắng nghe
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    temp_socket.bind(('0.0.0.0', 0))

                    temp_socket.sendto(b'PING', self.client_udp_addr)
                    
                    self.data_handler.handle_upload(temp_socket, save_filepath, self.transfer_type)
                    
                    temp_socket.close()
                    self.send_response(REPLY_226) 
                
                else:
                    self.send_response(REPLY_425) 
                    
            except socket.timeout:
                log_event(self.client_address, "!", f"STOR Timeout waiting for client data.")
                self.send_response(REPLY_426) 
            except Exception as e:
                log_event(self.client_address, "!", f"STOR Error: {e}")
                self.send_response(REPLY_426)

        elif cmd == "NLST":
            # 1. Xác định thư mục mục tiêu
            target_dir = self.current_dir
            if args:
                target_dir = os.path.abspath(os.path.join(self.current_dir, args)) if not os.path.isabs(args) else args

            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                self.send_response("550 Directory not found.")
                return
            
            self.send_response(REPLY_150)
            
            try:
                # 2. Lấy danh sách file/folder trong target_dir
                items = os.listdir(target_dir)
                list_data = "\r\n".join(items) + "\r\n" if items else ""
                
                # 3. Gửi danh sách qua kênh RDT UDP
                if self.data_mode == "PASV" and self.pasv_udp_socket:
                    self.pasv_udp_socket.settimeout(3.0)
                    _, client_udp_addr = self.pasv_udp_socket.recvfrom(1024)
                    
                    self.data_handler.rdt_channel.send_data_rdt(
                        self.pasv_udp_socket, client_udp_addr, list_data.encode('utf-8')
                    )
                    self.pasv_udp_socket.close()
                    self.pasv_udp_socket = None
                    
                elif self.data_mode == "PORT" and self.client_udp_addr:
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.data_handler.rdt_channel.send_data_rdt(temp_socket, self.client_udp_addr, list_data.encode('utf-8'))
                    temp_socket.close()
                
                self.send_response(REPLY_226)
            except Exception as e:
                self.send_response(REPLY_426)
                log_event(self.client_address, "!", f"NLST Error: {e}")
            return

        elif cmd == "LIST":
            # 1. Xác định thư mục mục tiêu
            target_dir = self.current_dir
            if args:
                target_dir = os.path.abspath(os.path.join(self.current_dir, args)) if not os.path.isabs(args) else args

            if not os.path.exists(target_dir) or not os.path.isdir(target_dir):
                self.send_response("550 Directory not found.")
                return
            
            self.send_response(REPLY_150)

            try: 
                detail_lines = []
                # 2. Duyệt qua target_dir
                for name in os.listdir(target_dir):
                    full_p = os.path.join(target_dir, name)
                    is_dir = os.path.isdir(full_p)
                    size = os.path.getsize(full_p) if not is_dir else 0
                    mode_str = "drwxr-xr-x" if is_dir else "-rw-r--r--"
                    detail_lines.append(f"{mode_str} 1 owner group {size:>8} {name}")

                list_data = "\r\n".join(detail_lines) + "\r\n" if detail_lines else ""

                # 3. Gửi danh sách qua kênh RDT UDP
                if self.data_mode == "PASV" and self.pasv_udp_socket:
                    self.pasv_udp_socket.settimeout(3.0)
                    _, client_udp_addr = self.pasv_udp_socket.recvfrom(1024)
                    self.data_handler.rdt_channel.send_data_rdt(self.pasv_udp_socket, client_udp_addr, list_data.encode('utf-8'))
                    self.pasv_udp_socket.close()
                    self.pasv_udp_socket = None
                    
                elif self.data_mode == "PORT" and self.client_udp_addr:
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    self.data_handler.rdt_channel.send_data_rdt(temp_socket, self.client_udp_addr, list_data.encode('utf-8'))
                    temp_socket.close()
                
                self.send_response(REPLY_226)
            except Exception as e:
                self.send_response(REPLY_426)
                log_event(self.client_address, "!", f"LIST Error: {e}")
            return
        
        elif cmd == "PWD": 
            virtual_path = self.current_dir.replace(SERVER_ROOT, "").replace("\\", "/")
            if virtual_path == "":
                virtual_path = "/"

            self.send_response(REPLY_257.format(virtual_path))

        elif cmd == "CWD":
            # Xử lý đặc biệt nếu arg là ".." để lùi về thư mục cha (CDUP logic)
            if args == "..":
                new_path = os.path.abspath(os.path.join(self.current_dir, ".."))
            else:
                new_path = os.path.abspath(os.path.join(self.current_dir, args))
            
            if not new_path.startswith(SERVER_ROOT):
                self.send_response(REPLY_550) 
            elif os.path.isdir(new_path):
                self.current_dir = new_path
                self.send_response(REPLY_250) 
            else:
                self.send_response(REPLY_550) 

        elif cmd == "CDUP":
            new_path = os.path.abspath(os.path.join(self.current_dir, ".."))

            if not new_path.startswith(SERVER_ROOT):
                self.send_response(REPLY_550)

            elif os.path.isdir(new_path):
                self.current_dir = new_path
                self.send_response(REPLY_250)

            else:
                self.send_response(REPLY_550)
                
        elif cmd == "MKD":
            new_path = os.path.abspath(os.path.join(self.current_dir, args))
            
            if not new_path.startswith(SERVER_ROOT):
                self.send_response(REPLY_550)

            elif not os.path.exists(new_path):
                try:
                    os.makedirs(new_path)
                    self.send_response(REPLY_250)
                except Exception as e:
                    self.send_response(REPLY_550)
            else:
                self.send_response(REPLY_550)

        elif cmd == "RMD":
            target_path = os.path.abspath(os.path.join(self.current_dir, args))

            if not target_path.startswith(SERVER_ROOT):
                self.send_response(REPLY_550)
            elif os.path.isdir(target_path):
                try:
                    os.rmdir(target_path)
                    self.send_response(REPLY_250)
                except Exception as e:
                    self.send_response(REPLY_550)
            else:
                self.send_response(REPLY_550)

        else: 
            self.send_response(REPLY_500)
