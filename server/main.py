import socket
import threading
import os
import sys

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from server.server_core import ClientHandler
from server.server_data import log_event

HOST = '0.0.0.0'
PORT = 2121

is_server_running = True

def start_server():
    global is_server_running

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST,PORT))
    server_socket.listen(5)
    server_socket.settimeout(1.0)
    log_event(None, "+", f"FTP Server initialized successfully. Listening on TCP {HOST}:{PORT}...")
    log_event(None, "*", "Shortcut: Press Ctrl+C to quickly shut down the server.")

    try:
        while is_server_running:
            try:
                client_sock, client_addr = server_socket.accept()
                client_sock.settimeout(None)
            except socket.timeout:
                continue
            except OSError:
                break

            log_event(None, "*", f"New client connected: {client_addr}")

            handler = ClientHandler(client_sock, client_addr)

            client_thread = threading.Thread(
                target=handler.run,
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        log_event(None, "-", "Server interrupted by user.")

    finally:
        is_server_running = False

        if server_socket:
            try:
                server_socket.close()
            except OSError:
                pass

        log_event(None, "-", "Server stopped.")

if __name__ == "__main__":
    start_server()