import socket
import threading
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from server.server_core import ClientHandler

HOST = '0.0.0.0'
PORT = 2121

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST,PORT))
    server_socket.listen(5)
    print(f"[*] FTP server is listening on TCP {HOST}:{PORT}...")

    try:
        while True:
            client_sock, client_add = server_socket.accept()
            print(f"[*] New client connected: {client_add}")

            handler = ClientHandler(client_sock, client_add)
            client_thread = threading.Thread(target=handler.run, daemon=True)
            client_thread.start()

    except KeyboardInterrupt:
        print ("\n[-] Server is shutting down...")

    finally: server_socket.close()

if __name__ == "__main__":
    start_server()