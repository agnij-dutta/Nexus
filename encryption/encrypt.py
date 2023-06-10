import json
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import base64

def encrypt_dict(data: dict, key: str) -> bytes:
    """
    Encrypts a dictionary using a key with AES encryption.
    """
    key = key.encode()
    data = str(data).encode()
    iv = get_random_bytes(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    return iv + encrypted_data


def decrypt_dict(data: bytes, key: str) -> dict:
    """
    Decrypts a dictionary using a key with AES encryption.
    """
    key = key.encode()
    iv = data[:AES.block_size]
    data = data[AES.block_size:]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(data), AES.block_size)
    return eval(decrypted_data.decode())



if __name__ == '__main__':
    # define the encryption key and dictionary to encrypt
    # key = "esmmb5r8u6zveps5"
    # dict_to_encrypt = {
    #         "key": "esmmb5r8u6zveps5",
    #         "contacts": str({})    
    #     }

    # # encrypt the dictionary
    # encrypted_dict = encrypt_dict(json.dumps(dict_to_encrypt), key)
    # encrypted_dict = base64.b64encode(encrypted_dict).decode()

    # # print the encrypted dictionary
    # print(encrypted_dict)

    # # decrypt the dictionary
    encrypted_dict = 'M+uolrxCgP6hhOquCjlwQfB8pFCVsBsNKkwXTnG6jLhQFPN3pNExWaZfVEjHxR1tGQboxgOqnnh1co5U8TaIh62I8YjzaCEX5FX9UNaZwseoxthlzKDC8TJHjuviCrGV'
    encrypted_dict = base64.b64decode(encrypted_dict)
    decrypted_dict = decrypt_dict(encrypted_dict, key='040kakuksksk5hs6')

    # print the decrypted dictionary
    print(decrypted_dict)
