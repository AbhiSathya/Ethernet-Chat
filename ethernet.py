import socket
import struct
import random
import threading
from utils import mac_str_to_bytes, bytes_to_mac_str
import netifaces

ETH_TYPE = b'\x88\xb5'
CHUNK_SIZE = 1400
TYPE_TEXT = 0x01
TYPE_FILE = 0x02

class EthernetCommunicator:
    def __init__(self, interface):
        self.interface = interface
        self.src_mac = mac_str_to_bytes(netifaces.ifaddresses(interface)[netifaces.AF_LINK][0]['addr'])
        self.sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.ntohs(0x0003))
        self.sock.bind((interface, 0))
        self.recv_callbacks = []
        self._stop_event = threading.Event()
        self.received_messages = {}

    def send_message(self, dst_mac_str, data_bytes, msg_type, progress_callback=None):
        dst_mac = mac_str_to_bytes(dst_mac_str)
        msg_id = random.getrandbits(32).to_bytes(4, 'big')
        total_chunks = (len(data_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE

        for i in range(total_chunks):
            chunk = data_bytes[i*CHUNK_SIZE:(i+1)*CHUNK_SIZE]
            header = struct.pack('!B4sHH', msg_type, msg_id, i, total_chunks)
            frame = dst_mac + self.src_mac + ETH_TYPE + header + chunk
            self.sock.send(frame)
            if progress_callback:
                progress_callback(i + 1, total_chunks)

    def add_receive_callback(self, callback):
        """callback signature: (src_mac, dst_mac, msg_type, full_data)"""
        self.recv_callbacks.append(callback)

    def stop(self):
        self._stop_event.set()

    def receive_loop(self):
        while not self._stop_event.is_set():
            raw_data, _ = self.sock.recvfrom(65535)
            if raw_data[12:14] != ETH_TYPE:
                continue

            dst_mac = bytes_to_mac_str(raw_data[0:6])
            src_mac = bytes_to_mac_str(raw_data[6:12])
            payload = raw_data[14:]

            if len(payload) < 9:
                continue

            msg_type = payload[0]
            msg_id = payload[1:5]
            chunk_num = struct.unpack('!H', payload[5:7])[0]
            total_chunks = struct.unpack('!H', payload[7:9])[0]
            data = payload[9:]

            key = msg_id.hex()
            if key not in self.received_messages:
                self.received_messages[key] = {
                    'type': msg_type,
                    'chunks': {},
                    'total': total_chunks,
                    'src_mac': src_mac,
                    'dst_mac': dst_mac,
                }

            self.received_messages[key]['chunks'][chunk_num] = data

            if len(self.received_messages[key]['chunks']) == total_chunks:
                # Reassemble
                chunks = self.received_messages[key]['chunks']
                full_data = b''.join(chunks[i] for i in range(total_chunks))
                # Notify callbacks
                for cb in self.recv_callbacks:
                    cb(src_mac, dst_mac, msg_type, full_data)
                del self.received_messages[key]

