import socket
import sys
import os

from shared.rdt_data_channel import RDTDataChannel

def log_event(client_addr, event_type: str, message: str):
    addr_str = f"[{client_addr[0]}:{client_addr[1]}]" if client_addr else "[SYSTEM]"
    print(f"{addr_str} [{event_type}] {message}", flush=True)

class ServerDataHandler:
    def __init__(self, client_control_addr):
        self.rdt_channel = RDTDataChannel()
        self.client_addr = client_control_addr

    def server_error(self, message):
        log_event(self.client_addr, "!", f"{message}")

    def handle_download(self, udp_socket: socket.socket, client_udp_addr: tuple, filepath: str, transfer_type: str):
        file_bytes = self.rdt_channel.read_file_payload(filepath, transfer_type)
        
        def server_download_progress(transferred, total, seq):
            log_event(self.client_addr, "~", f"Sent Packet Seq={seq} ({transferred}/{total} Bytes)")

        self.rdt_channel.send_data_rdt(udp_socket, client_udp_addr, file_bytes, progress_callback=server_download_progress, error_callback=self.server_error)
        log_event(self.client_addr, "~", "All data has been transferred securely!")

    def handle_upload(self, udp_socket: socket.socket, save_filepath: str, transfer_type: str):
        def server_upload_progress(received_bytes, total, seq):
            log_event(self.client_addr, "~", f"Received Seq={seq} -> Total: {received_bytes} Bytes")

        raw_bytes = self.rdt_channel.receive_data_rdt(udp_socket, progress_callback=server_upload_progress, error_callback=self.server_error)
        log_event(self.client_addr, "~", "Data transmission has ended. Reception complete!")
        self.rdt_channel.write_file_payload(save_filepath, raw_bytes, transfer_type)