import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging


class EncryptionManager:
    def __init__(self, key_file_path: str = "config/secret.key"):
        self.key_file_path = key_file_path
        self.logger = logging.getLogger(__name__)
        self.key = self._load_or_generate_key()
        self.fernet = Fernet(self.key)
    
    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one"""
        try:
            if os.path.exists(self.key_file_path):
                with open(self.key_file_path, 'rb') as key_file:
                    key = key_file.read()
                self.logger.info("Encryption key loaded from file")
                return key
            else:
                # Generate new key
                key = Fernet.generate_key()
                os.makedirs(os.path.dirname(self.key_file_path), exist_ok=True)
                with open(self.key_file_path, 'wb') as key_file:
                    key_file.write(key)
                self.logger.info("New encryption key generated and saved")
                return key
        except Exception as e:
            self.logger.error(f"Error handling encryption key: {str(e)}")
            raise e
    
    def encrypt_file(self, input_path: str, output_path: str = None) -> bool:
        """
        Encrypt a file using AES-256 (via Fernet)
        Returns: True if successful, False otherwise
        """
        try:
            if output_path is None:
                output_path = input_path + ".enc"
                
            with open(input_path, 'rb') as file:
                file_data = file.read()
            
            encrypted_data = self.fernet.encrypt(file_data)
            
            with open(output_path, 'wb') as file:
                file.write(encrypted_data)
            
            self.logger.info(f"File encrypted successfully: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {str(e)}")
            return False
    
    def decrypt_file(self, input_path: str, output_path: str = None) -> bool:
        """
        Decrypt a file using AES-256 (via Fernet)
        Returns: True if successful, False otherwise
        """
        try:
            if output_path is None:
                if input_path.endswith('.enc'):
                    output_path = input_path[:-4]  # Remove .enc extension
                else:
                    output_path = input_path + ".dec"
                    
            with open(input_path, 'rb') as file:
                encrypted_data = file.read()
            
            decrypted_data = self.fernet.decrypt(encrypted_data)
            
            with open(output_path, 'wb') as file:
                file.write(decrypted_data)
            
            self.logger.info(f"File decrypted successfully: {input_path} -> {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {str(e)}")
            return False
    
    def generate_key_from_password(self, password: str, salt: bytes = None) -> bytes:
        """Generate encryption key from password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
