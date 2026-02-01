import os
import zipfile
import shutil
import logging
from typing import Optional
from app.security.encryption import EncryptionManager
from app.security.integrity import IntegrityManager


class RestoreEngine:
    def __init__(self, config: dict):
        self.storage_dir = config["backup"]["storage_directory"]
        self.restore_dir = config["backup"]["restore_directory"]
        self.encryption_enabled = config["backup"].get("encryption_enabled", False)
        self.config = config
        self.setup_logging()
        
        if self.encryption_enabled:
            key_file = config["security"]["encryption_key_file"]
            self.encryption_manager = EncryptionManager(key_file)
            self.integrity_manager = IntegrityManager()
    
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    
    def restore_backup(self, backup_filename: str, stored_checksum: str = None) -> bool:
        """
        Restore backup from ZIP file to restore directory
        Returns: True if successful, False otherwise
        """
        try:
            backup_path = os.path.join(self.storage_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                self.logger.error(f"Backup file not found: {backup_filename}")
                return False
            
            # Handle encrypted files
            temp_file = None
            if backup_filename.endswith(".enc"):
                if not self.encryption_enabled:
                    self.logger.error("Encryption not enabled but encrypted file provided")
                    return False
                
                # Decrypt to temporary file
                temp_file = backup_path.replace(".enc", "_temp.zip")
                if not self.encryption_manager.decrypt_file(backup_path, temp_file):
                    self.logger.error(f"Decryption failed for: {backup_filename}")
                    return False
                
                backup_path = temp_file
            
            # Verify checksum if provided
            if stored_checksum:
                # For encrypted files, verify against the original encrypted file
                file_to_verify = os.path.join(self.storage_dir, backup_filename)
                if not self.integrity_manager.verify_checksum(file_to_verify, stored_checksum):
                    self.logger.error(f"Checksum verification failed for: {backup_filename}")
                    if temp_file and os.path.exists(temp_file):
                        os.remove(temp_file)
                    return False
                self.logger.info(f"Checksum verification passed for: {backup_filename}")
            
            # Clear restore directory if it exists
            if os.path.exists(self.restore_dir):
                shutil.rmtree(self.restore_dir)
            
            # Create restore directory
            os.makedirs(self.restore_dir, exist_ok=True)
            
            # Extract ZIP file
            self.logger.info(f"Restoring backup: {backup_filename}")
            
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(self.restore_dir)
            
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            self.logger.info(f"Backup restored successfully to: {self.restore_dir}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {str(e)}")
            # Clean up temporary file on error
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            return False
