import struct

class RDTPacket:
    def __init__(self, seq_num, flags, data=b''):
        self.seq_num = seq_num
        self.flags = flags
        self.payload = data
        self.payload_len = len(data)
        self.checksum = 0
           
    def to_bytes(self) -> bytes:
        self.checksum = self.calculate_checksum(self.payload)
        header = struct.pack('!IHHH', self.seq_num, self.flags, self.payload_len, self.checksum)
        return header + self.payload
    
    @staticmethod   # giong static trong class C++
    def calculate_checksum(data: bytes) -> int:
        if len(data) % 2 == 1:
            data += b'\x00'    # cong them byte cuoi cung neu le
        checksum = 0
        for i in range(0, len(data), 2):
            word = (data[i] << 8) + data[i+1]   # gom cap 2 byte (16-bit)
            checksum += word
            checksum = (checksum & 0xFFFF) + (checksum >> 16)   # cong bit tran vao nguoc lai hang don vi
        return (~checksum) & 0xFFFF     # Bu 1
    
    @staticmethod
    def from_bytes(packet_bytes: bytes):
        header_size = 10         # 4 byte Seq + 2 bytes Flags + 2 bytes Payload len + 2 bytes Checksum
        if len(packet_bytes) < header_size:
            return None
            
        seq_num, flags, payload_len, checksum = struct.unpack('!IHHH', packet_bytes[:header_size])
        payload = packet_bytes[header_size:header_size + payload_len]
        
        calculated = RDTPacket.calculate_checksum(payload)
        if calculated != checksum:
            print("[!] CẢNH BÁO: Gói tin bị lỗi bit (Checksum không khớp)!")
            return None 
            
        packet = RDTPacket(seq_num, flags, payload)
        packet.checksum = checksum
        return packet