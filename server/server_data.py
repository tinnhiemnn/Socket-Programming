import socket
import sys
import os

from shared.rdt_data_channel import RDTDataChannel

def log_event(client_addr, event_type: str, message: str):
    addr_str = f"[{client_addr[0]}:{client_addr[1]}]" if client_addr else "[SYSTEM]"
    print(f"{addr_str} [{event_type}] {message}", flush=True)

class ServerDataHandler:
    def __init__(self):
        self.rdt_channel = RDTDataChannel()

    def handle_download(self, udp_socket: socket.socket, client_udp_addr: tuple, filepath: str, transfer_type: str):
        file_bytes = self.rdt_channel.read_file_payload(filepath, transfer_type)
        def server_download_progress(transferred, total, addr, seq):
            log_event(addr, "~", f"Sent Packet Seq={seq} ({transferred}/{total} Bytes)")
        self.rdt_channel.send_data_rdt(udp_socket, client_udp_addr, file_bytes, progress_callback=server_download_progress)
        log_event(client_udp_addr, "~", "All data has been transferred securely!")

    def handle_upload(self, udp_socket: socket.socket, save_filepath: str, transfer_type: str):
        def server_upload_progress(received_bytes, total_bytes, addr, seq):
            log_event(addr, "~", f"Received Seq={seq} -> Total: {received_bytes} Bytes")
        raw_bytes = self.rdt_channel.receive_data_rdt(udp_socket, progress_callback=server_upload_progress)
        self.rdt_channel.write_file_payload(save_filepath, raw_bytes, transfer_type)