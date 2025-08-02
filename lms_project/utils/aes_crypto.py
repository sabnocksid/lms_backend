# utils/aes_crypto.py
from Crypto.Cipher import AES
import os
import hashlib

# user key based on  user id
def get_user_key(user):
    return hashlib.sha256(f"secret-key-{user.id}".encode()).digest()


#encryption function for a file
def encrypt_stream_for_user(user, input_stream, output_path):
    key = get_user_key(user)
    iv = os.urandom(16)
    cipher = AES.new(key, AES.MODE_CFB, iv=iv)

    with open(output_path, "wb") as f_out:
        f_out.write(iv)
        while True:
            chunk = input_stream.read(4096)
            if not chunk:
                break
            f_out.write(cipher.encrypt(chunk))

#decryption function for a file
def decrypt_file_for_user(user, input_path, output_path):
    key = get_user_key(user)

    with open(input_path, "rb") as f_in:
        iv = f_in.read(16)
        cipher = AES.new(key, AES.MODE_CFB, iv=iv)
        with open(output_path, "wb") as f_out:
            while True:
                chunk = f_in.read(4096)
                if not chunk:
                    break
                f_out.write(cipher.decrypt(chunk))
