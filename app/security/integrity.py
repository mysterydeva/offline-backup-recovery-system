import hashlib
import os
import logging
from typing import Optional


class IntegrityManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_checksum(self, file_path: str) -> Optional[str]:
        """
        Generate SHA-256 checksum for a file
        Returns: checksum string or None if failed
        """
        try:
            sha256_hash = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                # Read file in chunks to handle large files
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            checksum = sha256_hash.hexdigest()
            self.logger.info(f"Checksum generated for {file_path}: {checksum}")
            return checksum
            
        except Exception as e:
            self.logger.error(f"Failed to generate checksum for {file_path}: {str(e)}")
            return None
    
    def verify_checksum(self, file_path: str, stored_hash: str) -> bool:
        """
        Verify file integrity by comparing checksums
        Returns: True if checksums match, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"File not found for checksum verification: {file_path}")
                return False
            
            current_hash = self.generate_checksum(file_path)
            
            if current_hash is None:
                self.logger.error(f"Failed to generate current checksum for {file_path}")
                return False
            
            is_valid = current_hash.lower() == stored_hash.lower()
            
            if is_valid:
                self.logger.info(f"Checksum verification passed for {file_path}")
            else:
                self.logger.warning(f"Checksum verification failed for {file_path}")
                self.logger.warning(f"Expected: {stored_hash}")
                self.logger.warning(f"Actual: {current_hash}")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Checksum verification error for {file_path}: {str(e)}")
            return False
    
    def generate_checksum_string(self, data: bytes) -> str:
        """
        Generate SHA-256 checksum for byte data
        Returns: checksum string
        """
        try:
            sha256_hash = hashlib.sha256()
            sha256_hash.update(data)
            return sha256_hash.hexdigest()
        except Exception as e:
            self.logger.error(f"Failed to generate checksum for data: {str(e)}")
            return ""
    
    def verify_data_checksum(self, data: bytes, stored_hash: str) -> bool:
        """
        Verify data integrity by comparing checksums
        Returns: True if checksums match, False otherwise
        """
        try:
            current_hash = self.generate_checksum_string(data)
            return current_hash.lower() == stored_hash.lower()
        except Exception as e:
            self.logger.error(f"Data checksum verification error: {str(e)}")
            return False
