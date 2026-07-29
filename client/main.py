import os
import sys 

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from client.client_core import Client

def main():
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 2121 
    
    client = Client(SERVER_IP, SERVER_PORT)
    client.connect_control_channel()
    
    while True:
        try:
            user_input = input("ftp-client> ").strip()
            
            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].upper()

            if cmd in ["USER", "PASS"]:
                response = client.send_command(user_input)
                print(f"Server: {response.strip()}")

            elif cmd == "TYPE":
                if len(parts) > 1:
                    type_mode = parts[1].upper()
                    response = client.set_type(type_mode)
                    print(f"Server: {response.strip()}")
                else:
                    print("[!] Correct syntax: TYPE A or TYPE I")

            elif cmd == "RETR":
                # Cú pháp CLI: RETR <file_tren_server> <file_luu_o_client>
                if len(parts) >= 3:
                    remote_file = parts[1]
                    local_save_path = parts[2]
                    print(f"[*] Downloading '{remote_file}' by UDP RDT...")
                    response = client.download_file(remote_file, local_save_path)
                    print(f"Server: {response.strip()}")
                else:
                    print("[!] Correct syntax: RETR <remote_filename> <local_save_path>")

            elif cmd == "STOR":
                # Cú pháp CLI: STOR <file_local> <file_luu_tren_server>
                if len(parts) >= 3:
                    local_file = parts[1]
                    remote_save_name = parts[2]
                    if not os.path.exists(local_file):
                        print(f"[!] Local file '{local_file}' isn't exist!")
                        continue
                        
                    print(f"[*] Uploading '{local_file}' by UDP RDT...")
                    
                    response = client.upload_file(local_file, remote_save_name)
                    print(f"Server: {response.strip()}")
                else:
                    print("[!] Correct syntax: STOR <local_filepath> <remote_save_name>")

            elif cmd == "QUIT":
                response = client.send_command("QUIT")
                print(f"Server: {response.strip()}")
                client.control_socket.close()
                print("[*] Closing client app. Goodbye!")
                break

            else:
                response = client.send_command(user_input)
                print(f"Server: {response.strip()}")
            
        except KeyboardInterrupt:
            print("\n[*] Closing application.")
            break
        except Exception as e:
            print(f"[!] Error: {e}")

if __name__ == "__main__":
    main()