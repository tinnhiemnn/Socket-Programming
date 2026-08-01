import os
import socket
import time
from shared.rdt_packet import RDTPacket, FLAG_DATA, FLAG_ACK

class RDTDataChannel:
    def __init__(self, timeout=1.0, max_retries=5):
        self.timeout = timeout
        self.max_retries = max_retries

#   Hàm chia nhỏ dữ liệu và gửi đi bằng giải thuật Stop-and-Wait RDT
    def send_data_rdt(self, udp_socket: socket.socket, target_addr: tuple, data_bytes: bytes, progress_callback=None):
        CHUNK_SIZE = 1024  # Cắt dữ liệu thành từng khối 1KB
        chunks = [data_bytes[i:i+CHUNK_SIZE] for i in range(0, len(data_bytes), CHUNK_SIZE)]
        total_bytes = len(data_bytes)
        transferred_bytes = 0
        
        current_seq = 0
        udp_socket.settimeout(self.timeout)  

        for chunk in chunks:
            packet = RDTPacket(seq_num=current_seq, flags=FLAG_DATA, data=chunk)
            packet_bytes = packet.to_bytes()

            retries = 0
            ack_received = False

            while not ack_received and retries < self.max_retries:
                try:
                    # 1. Gửi gói tin qua UDP Socket
                    udp_socket.sendto(packet_bytes, target_addr)
                    #print(f"-> [UDP Sender] Packet Seq={current_seq}, Len={len(chunk)} has been sent.")

                    # 2. Đợi nhận gói ACK từ phía bên kia
                    resp_bytes, addr = udp_socket.recvfrom(2048)
                    ack_packet = RDTPacket.from_bytes(resp_bytes)

                    # 3. Kiểm tra xem có phải gói ACK hợp lệ không
                    if (ack_packet is not None and (ack_packet.flags & FLAG_ACK) and ack_packet.seq_num == current_seq):
                        #print(f"<- [UDP Sender] Received successfully ACK={current_seq}")
                        ack_received = True
                        current_seq += 1
                        transferred_bytes += len(chunk)

                        if progress_callback:
                            progress_callback(transferred_bytes, total_bytes, target_addr, current_seq)
                    else:
                        #print(f"[!] [UDP Sender] Invalid ACK, resending...")
                        retries += 1

                except socket.timeout:
                    # Xảy ra Timeout -> Báo lỗi và lặp lại vòng while để gửi lại
                    retries += 1
                    #print(f"[!] [UDP Sender] Timeout packet Seq={current_seq}! Retry ({retries}/{self.max_retries})...")

            if not ack_received:
                raise Exception(f"Disconnected: Loss of transmission of packet Seq={current_seq} after {self.max_retries} attempts.")
        

#   Hàm nhận các khối dữ liệu UDP và tự động phản hồi ACK bằng Stop-and-Wait
    def receive_data_rdt(self, udp_socket: socket.socket, expected_total_bytes: int = None, progress_callback = None) -> bytes:
        received_data = bytearray()
        expected_seq = 0
        udp_socket.settimeout(5.0) 
        start_time = time.time()

        while True:
            try:
                raw_bytes, sender_addr = udp_socket.recvfrom(2048)
                packet = RDTPacket.from_bytes(raw_bytes)

                # Trường hợp 1: Gói tin bị hỏng Checksum -> Bỏ qua, không gửi ACK[cite: 1]
                if packet is None:
                    #print("[!] [UDP Receiver] Received packet has checksum error -> Ignore.")
                    continue

                # Chỉ xử lý gói tin có cờ DATA
                if packet.flags & FLAG_DATA:
                    # Trường hợp 2: Nhận ĐÚNG gói tin đang chờ (Correct Seq)
                    if packet.seq_num == expected_seq:
                        received_data.extend(packet.payload)
                        
                        # Tạo gói phản hồi ACK
                        ack_pkt = RDTPacket(seq_num=expected_seq, flags=FLAG_ACK)
                        udp_socket.sendto(ack_pkt.to_bytes(), sender_addr)                        

                        if progress_callback:
                            progress_callback(len(received_data), expected_total_bytes, sender_addr, expected_seq)

                        expected_seq += 1

                        # Nếu đã nhận đủ số byte dự kiến (nếu biết trước) thì thoát vòng lặp
                        if expected_total_bytes and len(received_data) >= expected_total_bytes:
                            break

                    # Trường hợp 3: Nhận GÓI TRÙNG (Duplicate Seq - do ACK trước bị mất)
                    else:
                        #print(f"[*] [UDP Receiver] Received duplicate packet Seq={packet.seq_num} -> Resend ACK={packet.seq_num}")
                        # Không nối dữ liệu nữa, nhưng BẮT BUỘC gửi lại ACK tương ứng với gói vừa nhận
                        ack_pkt = RDTPacket(seq_num=packet.seq_num, flags=FLAG_ACK)
                        udp_socket.sendto(ack_pkt.to_bytes(), sender_addr)

            except socket.timeout:
                # Nếu một khoảng thời gian không thấy gói tin mới -> Giả định đã truyền xong
                #print("[*] [UDP Receiver] Data transmission has ended (Timeout). Reception complete!")
                break

        return bytes(received_data)

    @staticmethod
    def read_file_payload(filepath: str, transfer_type: str = 'I') -> bytes:
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File doesnot exist: {filepath}")

        if transfer_type.upper() == 'A':
            # TYPE A: Đọc dạng Text với mã hóa UTF-8, sau đó encode thành bytes
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                text_content = f.read()
                return text_content.encode('utf-8')
        else:
            # TYPE I: Đọc dạng Binary thô (Raw bytes)
            with open(filepath, 'rb') as f:
                return f.read()

    @staticmethod
    def write_file_payload(filepath: str, raw_bytes: bytes, transfer_type: str = 'I'):
        # Tạo thư mục chứa file nếu chưa tồn tại
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        if transfer_type.upper() == 'A':
            # TYPE A: Decode mảng bytes thành chuỗi text rồi ghi ở chế độ 'w'
            text_content = raw_bytes.decode('utf-8', errors='replace')
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(text_content)
        else:
            # TYPE I: Ghi trực tiếp mảng bytes thô ở chế độ 'wb'
            with open(filepath, 'wb') as f:
                f.write(raw_bytes)