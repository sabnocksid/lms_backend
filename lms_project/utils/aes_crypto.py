import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from django.core.files.storage import default_storage
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding

# AES key should be 32 bytes for AES-256
AES_KEY = os.environ.get("VIDEO_AES_KEY", os.urandom(32))

def encrypt_video_file(input_path, output_path):
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()

    with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
        f_out.write(iv)
        while chunk := f_in.read(1024 * 1024):
            padded_chunk = padder.update(chunk)
            f_out.write(encryptor.update(padded_chunk))
        f_out.write(encryptor.update(padder.finalize()))
        f_out.write(encryptor.finalize())

def decrypt_video_file(input_path, output_stream):
    with open(input_path, 'rb') as f:
        iv = f.read(16)
        cipher = Cipher(algorithms.AES(AES_KEY), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        unpadder = padding.PKCS7(128).unpadder()

        while chunk := f.read(1024 * 1024):
            decrypted_chunk = decryptor.update(chunk)
            output_stream.write(unpadder.update(decrypted_chunk))

        output_stream.write(unpadder.finalize())
        output_stream.write(decryptor.finalize())

def handle_video_upload(file, filename):
    temp_input_path = f"/tmp/{filename}"
    temp_encrypted_path = f"/tmp/encrypted_{filename}"

    # Save uploaded file to temp
    with open(temp_input_path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

    # Encrypt it
    encrypt_video_file(temp_input_path, temp_encrypted_path)

    # Save encrypted file to media storage
    final_path = default_storage.save(f"encrypted_videos/{filename}", open(temp_encrypted_path, 'rb'))

    # Cleanup temp files
    os.remove(temp_input_path)
    os.remove(temp_encrypted_path)

    return final_path