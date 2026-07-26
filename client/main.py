from client.client_core import Client

def main():
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 2121 
    
    client = Client(SERVER_IP, SERVER_PORT)
    client.connect_control_channel()
    
    while True:
        user_input = input("ftp-client> ").strip()
        
        if not user_input:
            continue
            
        response = client.send_command(user_input)
        print(response)
        
        if user_input.upper() == "QUIT" and "221" in response:
            print("[*] Closing client app. Goodbye!")
            client.control_socket.close()
            break

if __name__ == "__main__":
    main()