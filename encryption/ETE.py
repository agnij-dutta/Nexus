from cryptography.fernet import Fernet

class ETEEncryption:
    def __init__(self, key=None):
        if key is None:
            self.key = Fernet.generate_key()
        else:
            self.key = key
        
    def encrypt(self, plaintext):
        f = Fernet(self.key)
        ciphertext = f.encrypt(plaintext.encode())
        return ciphertext
        
    def decrypt(self, ciphertext):
        f = Fernet(self.key)
        plaintext = f.decrypt(ciphertext).decode()
        return plaintext

