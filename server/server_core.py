import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.protocol import *
from server.server_data import ServerDataHandler

class ClientHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        self.is_authenticated = False
        self.username = None
        self.is_running = True

        self.transfer_type = 'I' 
        self.data_handler = ServerDataHandler()
        self.pasv_udp_socket = None
        self.client_udp_addr = None

    def send_response(self, respone_str): 
        """Send an FTP response code to the client."""
        try: 
            self.client_socket.sendall(respone_str.encode('utf-8'))
        except Exception as e:
            print(f"[!] Error sending data to {self.client_address}: {e}")

    def run(self):
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

                print(f"[{self.client_address}] Recieve: {cmd} {args}")
                self.process_command(cmd, args)

            except Exception as e:
                print(f"[!] Connection lost with {self.client_address}: {e}")
                break

        self.client_socket.close()
        print(f"[-] Connection closed with {self.client_address}")

    def process_command(self, cmd, args):
        """Validate and process FTP commands."""
        if cmd == "USER":
            self.username = args
            self.send_response(REPLY_331)

        elif cmd == "PASS":
            if self.username:
                self.is_authenticated = True
                self.send_response(REPLY_230)
            else:
                self.send_response(REPLY_530)

        elif cmd == "QUIT":
            self.send_response(REPLY_221)
            self.is_running = False

        elif cmd == "TYPE":
            if args.upper() in ['A', 'I']:
                self.transfer_type = args.upper()
                self.send_response("REPLY_200\r\n")
            else:
                self.send_response("REPLY 504\r\n")

        elif cmd == "RETR": 
            filepath = os.path.join("storage/server_root", args)
            if not os.path.exists(filepath):
                self.send_response("REPLY 550\r\n")
            else:
                self.send_response("REPLY 150.\r\n")
                
                # 2. Nếu ở PASV Mode, nhận gói UDP mồi từ Client để lấy client_udp_addr
                if self.pasv_udp_socket:
                    self.pasv_udp_socket.settimeout(3.0)
                    _, client_udp_addr = self.pasv_udp_socket.recvfrom(1024)
                    
                    # 3. Server đóng vai UDP Sender đẩy file qua RDT
                    self.data_handler.handle_download(self.pasv_udp_socket, client_udp_addr, filepath, self.transfer_type)
                    self.pasv_udp_socket.close()
                    self.pasv_udp_socket = None

                # còn thiếu nếu ở PORT Mode
                
                # 4. Báo 226 Hoàn tất qua TCP
                self.send_response("REPLY_226.\r\n")

        elif cmd == "STOR": 
            save_filepath = os.path.join("storage/server_root", args)
            self.send_response("REPLY_150.\r\n")
            
            if self.pasv_udp_socket:
                self.data_handler.handle_upload(self.pasv_udp_socket, save_filepath, self.transfer_type)
                self.pasv_udp_socket.close()
                self.pasv_udp_socket = None

            # còn thiếu nếu ở PORT mode
            
            self.send_response("REPLY_226.\r\n")

        else: 
            if not self.is_authenticated:
                self.send_response(REPLY_530)
            else:
                self.send_response(REPLY_500)
