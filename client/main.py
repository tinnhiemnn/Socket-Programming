import os
import sys 

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from client.client_core import Client
from client.cli_formatter import print_header, print_status, COLOR_CYAN, COLOR_RESET, COLOR_BOLD

def print_help():
    print(f"\n{COLOR_BOLD}Available Commands:{COLOR_RESET}")
    print("  USER <username>       : Authenticate username")
    print("  PASS <password>       : Authenticate password")
    print("  PASV / PORT           : Switch Data Mode (Passive / Active)")
    print("  TYPE <A|I>            : Change Transfer Mode (A: ASCII, I: Binary)")
    print("  RETR <remote> <local> : Download file from Server via UDP RDT")
    print("  STOR <local> <remote> : Upload file to Server via UDP RDT")
    print("  LIST / NLST           : Get directory listing via UDP RDT")
    print("  PWD / CWD / CDUP      : Navigation commands")
    print("  MKD <dir> / RMD <dir> : Directory creation/deletion")
    print("  QUIT                  : Terminate session\n")

def main():
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 2121 
    
    print_header()
    client = Client(SERVER_IP, SERVER_PORT)
    client.connect_control_channel()
    print_help()
    
    while True:
        try:
            prompt = f"{COLOR_CYAN}{COLOR_BOLD}ftp-client [{client.data_mode}|TYPE-{client.transfer_type}]>{COLOR_RESET} "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].upper()

            if cmd in ["USER", "PASS"]:
                response = client.send_command(user_input)
                print_status(response.strip(), "NET")

            elif cmd == "TYPE":
                if len(parts) > 1:
                    type_mode = parts[1].upper()
                    response = client.set_type(type_mode)
                    print_status(response.strip(), "SUCCESS" if "200" in response else "ERROR")
                else:
                    print_status("Correct syntax: TYPE A or TYPE I", "WARNING")

            elif cmd == "RETR":
                # Cú pháp CLI: RETR <file_tren_server> <file_luu_o_client>
                if len(parts) >= 3:
                    remote_file = parts[1]
                    local_save_path = parts[2]
                    print_status(f"Downloading '{remote_file}' via UDP RDT...", "NET")
                    response = client.download_file(remote_file, local_save_path)
                    print_status(response.strip(), "SUCCESS" if "226" in response else "ERROR")
                else:
                    print_status("Correct syntax: RETR <remote_filename> <local_save_path>", "WARNING")

            elif cmd == "STOR":
                # Cú pháp CLI: STOR <file_local> <file_luu_tren_server>
                if len(parts) >= 3:
                    local_file = parts[1]
                    remote_save_name = parts[2]
                    if not os.path.exists(local_file):
                        print_status(f"Local file '{local_file}' does not exist!", "ERROR")
                        continue
                        
                    print_status(f"Uploading '{local_file}' via UDP RDT...", "NET")
                    response = client.upload_file(local_file, remote_save_name)
                    print_status(response.strip(), "SUCCESS" if "226" in response else "ERROR")
                else:
                    print_status("Correct syntax: STOR <local_filepath> <remote_save_name>", "WARNING")

            elif cmd == "QUIT":
                response = client.send_command("QUIT")
                print_status(response.strip(), "NET")
                client.control_socket.close()
                print_status("Session closed cleanly. Goodbye!", "INFO")
                break

            elif cmd == "PASV":
                client.enable_passive_mode()
                print_status("Switched to PASSIVE Data Mode.", "SUCCESS")

            elif cmd == "PORT":
                res = client.enable_active_mode()
                print_status(f"Switched to ACTIVE Data Mode. Server: {res.strip()}", "SUCCESS")

            elif cmd in ["LIST", "NLST"]:
                print_status(f"Fetching directory listing ({cmd}) via UDP RDT...", "NET")
                response = client.list_directory(cmd)
                print_status(response.strip(), "SUCCESS" if "226" in response else "ERROR")

            else:
                response = client.send_command(user_input)
                print_status(response.strip(), "NET")
            
        except KeyboardInterrupt:
            print_status("Closing client application.", "WARNING")
            break
        except Exception as e:
            print_status(f"Error: {e}", "ERROR")

if __name__ == "__main__":
    main()