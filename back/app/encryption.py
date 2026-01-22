from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()


class PasswordEncryption:
    
    def __init__(self):
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            print("WARNING: ENCRYPTION_KEY no encontrada. Generando una nueva...")
            encryption_key = Fernet.generate_key().decode()
            print(f"Agrega a tu .env: ENCRYPTION_KEY={encryption_key}")
        else:
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
        
        self.cipher = Fernet(encryption_key if isinstance(encryption_key, bytes) else encryption_key.encode())
    
    def encrypt(self, plaintext: str) -> str:
        if not plaintext:
            return None
        
        if isinstance(plaintext, str):
            plaintext = plaintext.encode()
        
        encrypted = self.cipher.encrypt(plaintext)
        return encrypted.decode()
    
    def decrypt(self, encrypted_text: str) -> str:
        if not encrypted_text:
            return None
        
        if isinstance(encrypted_text, str):
            encrypted_text = encrypted_text.encode()
        
        decrypted = self.cipher.decrypt(encrypted_text)
        return decrypted.decode()


password_encryptor = PasswordEncryption()


def encrypt_password(password: str) -> str:
    return password_encryptor.encrypt(password)


def decrypt_password(encrypted_password: str) -> str:
    return password_encryptor.decrypt(encrypted_password)
