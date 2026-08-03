import os
import sys 
import getpass

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from client.client_core import Client
from client.cli_formatter import print_header, print_status, COLOR_CYAN, COLOR_RESET, COLOR_BOLD

def print_help():
    print(f"\n{COLOR_BOLD}Available Commands:{COLOR_RESET}")
    print("  PASV / PORT           : Switch Data Mode (Passive / Active)")
    print("  TYPE <A|I>            : Change Transfer Mode (A: ASCII, I: Binary)")
    print("  RETR <remote> <local> : Download file from Server via UDP RDT")
    print("  STOR <local> <remote> : Upload file to Server via UDP RDT")
    print("  LIST [path]           : List detailed directory contents (default: current dir)")
    print("  NLST [path]           : List directory file names only (default: current dir)")
    print("  PWD / CWD / CDUP      : Navigation commands")
    print("  MKD <dir> / RMD <dir> : Directory creation/deletion")
    print("  HELP                  : Display this help message")
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
            username = input(f"{COLOR_CYAN}{COLOR_BOLD}Username:{COLOR_RESET} ").strip()
            response = client.send_command(f"USER {username}")
            if "530" in response:
                print_status("Invalid username. Please try again.", "ERROR")
            else:
                print_status(response.strip(), "SUCCESS")
                password = getpass.getpass(f"{COLOR_CYAN}{COLOR_BOLD}Password:{COLOR_RESET} ").strip()
                response = client.send_command(f"PASS {password}")
                if "530" in response:
                    print_status("Incorrect password. Please re-enter your username and password.", "ERROR")
                else:
                    print_status(response.strip(), "SUCCESS")
                    break
        except KeyboardInterrupt:
            print_status("Closing client application.", "WARNING")
            return
        except Exception as e:
            print_status(f"Error: {e}", "ERROR")

    
    while True:
        try:
            prompt = f"{COLOR_CYAN}{COLOR_BOLD}ftp-client [{client.data_mode}|TYPE-{client.transfer_type}]>{COLOR_RESET} "
            user_input = input(prompt).strip()
            
            if not user_input:
                continue

            parts = user_input.split()
            cmd = parts[0].upper()

            if cmd in ["USER", "PASS"]:
                print_status("Already logged in.", "WARNING")

            elif cmd == "TYPE":
                type_mode = parts[1].upper() if len(parts) > 1 else None
                response = client.set_type(type_mode)
                print_status(response.strip(), "SUCCESS" if "200" in response else "ERROR")

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
                if "200" in res:
                    print_status(f"Switched to ACTIVE Data Mode. Server: {res.strip()}", "SUCCESS")
                else:
                    print_status(f"Failed to enter Passive Mode. Server: {res.strip()}", "ERROR")

            elif cmd in ["LIST", "NLST"]:
                args = parts[1] if len(parts) > 1 else None
                print_status(f"Fetching directory listing ({cmd}) {args or ''} via UDP RDT...", "NET")
                response = client.list_directory(cmd, args)
                print_status(response.strip(), "SUCCESS" if "226" in response else "ERROR")

            elif cmd in ["CWD", "CDUP", "MKD", "RMD"]:
                response = client.send_command(user_input)
                print_status(response.strip(), "SUCCESS" if "250" in response else "ERROR")

            elif cmd == "HELP":
                print_help()

            else:
                response = client.send_command(user_input)
                print_status(response.strip(), "ERROR" if "500" in response else "NET")
            
        except KeyboardInterrupt:
            print_status("Closing client application.", "WARNING")
            break
        except Exception as e:
            print_status(f"Error: {e}", "ERROR")

if __name__ == "__main__":
    main()