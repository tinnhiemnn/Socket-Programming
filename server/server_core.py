import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.protocol import *

class ClientHandler:
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        self.is_authenticated = False
        self.username = None
        self.is_running = True

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

        else: 
            if not self.is_authenticated:
                self.send_response(REPLY_530)
            else:
                self.send_response(REPLY_500)
