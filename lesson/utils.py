from cryptography.fernet import Fernet
import base64
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def generate_key_from_user(user):
    password = str(user.id).encode()
    salt = b'static_salt_1234'
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return base64.urlsafe_b64encode(kdf.derive(password))


def encrypt_video_file(file_path, user):
    key = generate_key_from_user(user)
    fernet = Fernet(key)
    with open(file_path, "rb") as f:
        data = f.read()
    encrypted = fernet.encrypt(data)
    with open(file_path, "wb") as f:
        f.write(encrypted)
