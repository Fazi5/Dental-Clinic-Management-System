import os
import hashlib
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

def load_key():
    """Loads the key from the current directory or creates it if it doesn't exist."""
    if not os.path.exists(KEY_FILE):
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as key_file:
            key_file.write(key)
    else:
        with open(KEY_FILE, "rb") as key_file:
            key = key_file.read()
    return key

# Initialize Cipher
key = load_key()
cipher_suite = Fernet(key)

def encrypt_data(data: str) -> str:
    """Encrypts a string and returns a url-safe base64 encoded string."""
    if not data:
        return None
    return cipher_suite.encrypt(data.encode('utf-8')).decode('utf-8')

def decrypt_data(token: str) -> str:
    """Decrypts a token and returns the original string."""
    if not token:
        return None
    try:
        return cipher_suite.decrypt(token.encode('utf-8')).decode('utf-8')
    except Exception as e:
        print(f"Decryption error: {e}")
        return None

def hash_data(data: str) -> str:
    """Returns a SHA256 hash of the data for lookup purposes."""
    if not data:
        return None
    return hashlib.sha256(data.encode('utf-8')).hexdigest()
