alphabet = 'abcdefghijklmnopqrstuvwxyz'

def generate_vigenere_square(self):
        # Generate Vigenere square
        vigenere_square = []
        for i in range(26):
            row = alphabet[i:] + alphabet[:i]
            vigenere_square.append(row)
        return vigenere_square

def vigenere_encrypt(self, plaintext, key):
    # Encrypt plaintext using Vigenere cipher
    vigenere_square = self.generate_vigenere_square()
    ciphertext = ''
    key_index = 0
    for char in plaintext:
        if char.isalpha():
            row = vigenere_square[ord(key[key_index].lower()) - 97]
            column = row.index(char.lower())
            ciphertext += row[column]
            key_index = (key_index + 1) % len(key)
        else:
            ciphertext += char
    return ciphertext

def vigenere_decrypt(self, ciphertext, key):
    # Decrypt ciphertext using Vigenere cipher
    vigenere_square = generate_vigenere_square()
    plaintext = ''
    key_index = 0
    for char in ciphertext:
        if char.isalpha():
            row = vigenere_square[ord(key[key_index].lower()) - 97]
            column = row.index(char.lower())
            plaintext += alphabet[column]
            key_index = (key_index + 1) % len(key)
        else:
            plaintext += char
    return plaintext
