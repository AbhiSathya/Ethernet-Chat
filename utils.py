import base64

def mac_str_to_bytes(mac_str):
    return bytes.fromhex(mac_str.replace(':', ''))

def bytes_to_mac_str(mac_bytes):
    return ':'.join(f'{b:02x}' for b in mac_bytes)

def encode_file_to_base64(file_path):
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read())

def decode_base64_to_file(data_b64, save_path):
    with open(save_path, 'wb') as f:
        f.write(base64.b64decode(data_b64))

