import os
from utils.aes_crypto import encrypt_video_file 

def handle_video_upload(uploaded_file):
    input_path = f"/tmp/{uploaded_file.name}"
    encrypted_path = f"media/encrypted/{uploaded_file.name}.enc"

    with open(input_path, 'wb') as f:
        for chunk in uploaded_file.chunks():
            f.write(chunk)

    encrypt_video_file(input_path, encrypted_path)
    os.remove(input_path)

    return encrypted_path
