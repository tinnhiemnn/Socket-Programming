import socket
import sys
import os

from client.client_data import RDTDataChannel

class ServerDataHandler:
    def __init__(self):
        self.rdt_channel = RDTDataChannel()

    def handle_download(self, udp_socket: socket.socket, client_udp_addr: tuple, filepath: str, transfer_type: str):
        file_bytes = self.rdt_channel.read_file_payload(filepath, transfer_type)
        self.rdt_channel.send_data_rdt(udp_socket, client_udp_addr, file_bytes)

    def handle_upload(self, udp_socket: socket.socket, save_filepath: str, transfer_type: str):
        raw_bytes = self.rdt_channel.receive_data_rdt(udp_socket)
        self.rdt_channel.write_file_payload(save_filepath, raw_bytes, transfer_type)