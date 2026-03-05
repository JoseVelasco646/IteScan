from cryptography.fernet import Fernet
import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PasswordEncryption:
    
    def __init__(self):
        encryption_key = os.getenv("ENCRYPTION_KEY")
        
        if not encryption_key:
            logger.critical(
                "La variable de entorno ENCRYPTION_KEY no está definida. "
                "Sin esta clave, las contraseñas cifradas serán irrecuperables tras un reinicio. "
                'Genera una clave con: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())" '
                "Y añádela al archivo .env o como variable de entorno."
            )
            sys.exit(1)
        
        if isinstance(encryption_key, str):
            encryption_key = encryption_key.encode()
        
        self.cipher = Fernet(encryption_key)
    
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
