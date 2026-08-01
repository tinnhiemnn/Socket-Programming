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
server_socket = None

def listen_for_commands():
    """Luồng phụ lắng nghe lệnh từ bàn phím để tắt server nhanh"""
    global is_server_running, server_socket
    print("[*] Shortcut: Type 'q' or 'quit' and press Enter to quickly shut down the server.")
    while is_server_running:
        try:
            cmd = input().strip().lower()
            if cmd in ['q', 'quit', 'exit']:
                print("\n[*] The server is being shut down as requested from the keyboard...")
                is_server_running = False
                if server_socket:
                    try:
                        server_socket.close()
                    except:
                        pass
                break
        except EOFError:
            break

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    server_socket.bind((HOST,PORT))
    server_socket.listen(5)
    log_event(None, "+", f"FTP Server initialized successfully. Listening on TCP {HOST}:{PORT}...")

    try:
        while True:
            client_sock, client_add = server_socket.accept()
            log_event(None, "*", f"New client connected: {client_add}")

            handler = ClientHandler(client_sock, client_add)
            client_thread = threading.Thread(target=handler.run, daemon=True)
            client_thread.start()

    except KeyboardInterrupt:
        log_event(None, "!", "Server is shutting down manually...")
    except Exception as e:
        log_event(None, "!", f"Fatal server error: {e}")
    finally:
        if 'server_socket' in locals():
            server_socket.close()
        log_event(None, "-", "Server socket closed. Execution stopped.")

if __name__ == "__main__":
    start_server()