from Crypto.Cipher import DES

class DES2:
    def __init__(self, key) -> None:
            if isinstance(key, bytes) or isinstance(key, str):
                key = key.encode('utf-8') if isinstance(key, str) else key
                self.key1, self.key2 = split_key(key)
            else:
                raise TypeError("Key must be bytes or str")

    def encrypt(self, data):
        encipher = DES.new(self.key1, DES.MODE_ECB)
        data = padding(data)
        encrypted_data = encipher.encrypt(data)
        encipher = DES.new(self.key2, DES.MODE_ECB)
        data = padding(encrypted_data)
        encrypted_data = encipher.encrypt(data)
        return encrypted_data

    def decrypt(self, data):
        decipher = DES.new(self.key2, DES.MODE_ECB)
        decrypted_data = decipher.decrypt(data)
        decrypted_data = cut(decrypted_data)
        decipher = DES.new(self.key1, DES.MODE_ECB)
        decrypted_data = decipher.decrypt(decrypted_data)
        decrypted_data = cut(decrypted_data)
        return decrypted_data
    
def new_(key):
    return DES2(key)

def split_key(key):
    key_len = len(key)
    if key_len > 16:
        raise ValueError("key must be 16 bytes or less")
    elif key_len == 16:
        key1 = key[0::2]
        key2 = key[1::2]
        return key1, key2
    elif key_len < 8:
        raise ValueError("key must be 8 bytes or more")
    else:
        key += b'\0' * (16 - key_len)
        key1 = key[0::2]
        key2 = key[1::2]
        return key1, key2

def cut(data):
    data_len = len(data)
    index = -1
    for i, byte in enumerate(reversed(data)):
        if byte != 0x00:
            index = i
            break

    if index != -1:
        return data[:data_len - index]
    else:
        return data

def padding(data):
    block_size = DES.block_size
    data += b'\0' * (block_size - len(data) % block_size)
    return data