import struct

FLAG_DATA = 0x0001  # Gói tin chứa dữ liệu
FLAG_ACK  = 0x0002  # Gói tin phản hồi xác nhận

class RDTPacket:
    def __init__(self, seq_num, flags, data=b''):
        self.seq_num = seq_num
        self.flags = flags
        self.payload = data
        self.payload_len = len(data)
        self.checksum = 0
           
    def to_bytes(self) -> bytes:
        header = struct.pack('!IHHH', self.seq_num, self.flags, self.payload_len, 0)
        self.checksum = self.calculate_checksum(header + self.payload)
        header = struct.pack('!IHHH', self.seq_num, self.flags, self.payload_len, self.checksum)
        return header + self.payload
    
    @staticmethod   # Giống static trong class C++
    def calculate_checksum(data: bytes) -> int:
        if len(data) % 2 == 1:
            data += b'\x00'    # Cộng thêm byte cuối cùng nếu lẻ
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i+1]   # Gôm cặp 2 byte (16-bit)
            checksum += word
            checksum = (checksum & 0xFFFF) + (checksum >> 16)   # Cộng bit bị tràn vào ngược lại hàng đơn vị
        return (~checksum) & 0xFFFF     # Bu 1
    
    @staticmethod
    def from_bytes(packet_bytes: bytes):
        header_size = 10         # 4 byte Seq + 2 bytes Flags + 2 bytes Payload len + 2 bytes Checksum
        if len(packet_bytes) < header_size:
            return None
            
        if RDTPacket.calculate_checksum(packet_bytes) != 0:
            print("[!] WARNING: Packet has a bit error (Checksum does not match)!")
            return None 
        
        seq_num, flags, payload_len, checksum = struct.unpack('!IHHH', packet_bytes[:header_size])
        payload = packet_bytes[header_size:header_size + payload_len]
            
        packet = RDTPacket(seq_num, flags, payload)
        packet.checksum = checksum
        return packet