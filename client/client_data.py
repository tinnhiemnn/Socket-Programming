import socket
import sys
import os

from shared.rdt_data_channel import RDTDataChannel
from client.cli_formatter import print_progress_bar, print_status

class ClientDataHandler:
    def __init__(self):
        self.rdt_channel = RDTDataChannel()

    def handle_upload(self, udp_socket: socket.socket, client_udp_addr: tuple, filepath: str, transfer_type: str):
        file_bytes = self.rdt_channel.read_file_payload(filepath, transfer_type)

        def client_upload_progress(transferred, total, addr, seq):
            print_progress_bar(transferred, total, speed_bps=1024*1024)

        self.rdt_channel.send_data_rdt(udp_socket, client_udp_addr, file_bytes, progress_callback=client_upload_progress)
        print_status("All data has been transferred securely!", "NET")

    def handle_download(self, udp_socket: socket.socket, save_filepath: str, transfer_type: str):
        def client_download_progress(received_bytes, total_bytes, addr, seq):
            print_progress_bar(received_bytes, total_bytes, speed_bps=1024*1024)

        raw_bytes = self.rdt_channel.receive_data_rdt(udp_socket, progress_callback=client_download_progress)
        self.rdt_channel.write_file_payload(save_filepath, raw_bytes, transfer_type)