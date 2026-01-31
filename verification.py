"""
Backup Verification Module - Phase-3 Enhancement
Automatically verifies backups by restoring to sandbox environment
"""

import os
import shutil
import zipfile
import logging
from datetime import datetime
from typing import Dict, Optional, List
from security.encryption import EncryptionManager
from security.integrity import IntegrityManager


class BackupVerificationEngine:
    """Backup verification engine with sandbox restore testing"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.sandbox_dir = config.get('verification', {}).get('sandbox_directory', 'sandbox_restore')
        self.encryption_manager = EncryptionManager()
        self.integrity_manager = IntegrityManager()
    
    def verify_backup(self, backup_file: str, checksum: str, encrypted: bool = False) -> Dict:
        """Verify a backup by restoring to sandbox"""
        verification_result = {
            'verified': False,
            'timestamp': datetime.now().isoformat(),
            'errors': [],
            'warnings': [],
            'files_restored': 0,
            'integrity_check': False,
            'encryption_check': False
        }
        
        try:
            # Clean up existing sandbox
            self._cleanup_sandbox()
            
            # Create sandbox directory
            os.makedirs(self.sandbox_dir, exist_ok=True)
            
            # Step 1: Verify file integrity
            if checksum:
                integrity_valid = self.integrity_manager.verify_checksum(backup_file, checksum)
                verification_result['integrity_check'] = integrity_valid
                
                if not integrity_valid:
                    verification_result['errors'].append("Checksum verification failed")
                    self.logger.error(f"Backup verification failed: checksum mismatch for {backup_file}")
                    return verification_result
            else:
                verification_result['warnings'].append("No checksum available for verification")
            
            # Step 2: Decrypt if necessary
            temp_file = backup_file
            if encrypted:
                try:
                    temp_file = backup_file.replace('.enc', '_temp.zip')
                    decrypt_success = self.encryption_manager.decrypt_file(backup_file, temp_file)
                    verification_result['encryption_check'] = decrypt_success
                    
                    if not decrypt_success:
                        verification_result['errors'].append("Decryption failed")
                        self.logger.error(f"Backup verification failed: decryption failed for {backup_file}")
                        return verification_result
                except Exception as e:
                    verification_result['errors'].append(f"Decryption error: {str(e)}")
                    self.logger.error(f"Backup verification failed: decryption error for {backup_file}: {str(e)}")
                    return verification_result
            
            # Step 3: Extract to sandbox
            try:
                files_restored = self._extract_to_sandbox(temp_file)
                verification_result['files_restored'] = files_restored
                
                if files_restored == 0:
                    verification_result['errors'].append("No files extracted from backup")
                    self.logger.error(f"Backup verification failed: no files extracted from {backup_file}")
                    return verification_result
                    
            except Exception as e:
                verification_result['errors'].append(f"Extraction error: {str(e)}")
                self.logger.error(f"Backup verification failed: extraction error for {backup_file}: {str(e)}")
                return verification_result
            
            # Step 4: Verify key files exist
            missing_files = self._verify_key_files()
            if missing_files:
                verification_result['warnings'].append(f"Missing key files: {missing_files}")
                self.logger.warning(f"Backup verification warning: missing key files {missing_files}")
            
            # Step 5: Verify file structure
            structure_valid = self._verify_file_structure()
            if not structure_valid:
                verification_result['warnings'].append("File structure verification failed")
                self.logger.warning("Backup verification warning: file structure issues detected")
            
            # Step 6: Check for corruption
            corruption_issues = self._check_file_corruption()
            if corruption_issues:
                verification_result['errors'].extend(corruption_issues)
                self.logger.error(f"Backup verification failed: corruption detected in {len(corruption_issues)} files")
                return verification_result
            
            # If we got here, verification passed
            verification_result['verified'] = True
            self.logger.info(f"Backup verification successful: {backup_file}")
            
        except Exception as e:
            verification_result['errors'].append(f"Verification error: {str(e)}")
            self.logger.error(f"Backup verification error for {backup_file}: {str(e)}")
        
        finally:
            # Clean up temporary files
            if 'temp_file' in locals() and temp_file != backup_file and os.path.exists(temp_file):
                os.remove(temp_file)
            
            # Keep sandbox for manual inspection if verification failed
            if verification_result['verified']:
                self._cleanup_sandbox()
        
        return verification_result
    
    def _cleanup_sandbox(self):
        """Clean up sandbox directory"""
        if os.path.exists(self.sandbox_dir):
            try:
                shutil.rmtree(self.sandbox_dir)
                self.logger.debug(f"Sandbox cleaned up: {self.sandbox_dir}")
            except Exception as e:
                self.logger.warning(f"Failed to cleanup sandbox: {str(e)}")
    
    def _extract_to_sandbox(self, backup_file: str) -> int:
        """Extract backup file to sandbox directory"""
        files_count = 0
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                zip_ref.extractall(self.sandbox_dir)
                files_count = len(zip_ref.namelist())
                self.logger.debug(f"Extracted {files_count} files to sandbox")
                
        except zipfile.BadZipFile as e:
            raise Exception(f"Invalid ZIP file: {str(e)}")
        except Exception as e:
            raise Exception(f"Extraction failed: {str(e)}")
        
        return files_count
    
    def _verify_key_files(self) -> List[str]:
        """Verify that key files exist in restored backup"""
        missing_files = []
        
        # Define key files that should exist
        key_files = [
            'index.html',
            'config.json',
            'README.md',
            'requirements.txt'
        ]
        
        for key_file in key_files:
            file_path = os.path.join(self.sandbox_dir, key_file)
            if not os.path.exists(file_path):
                missing_files.append(key_file)
        
        return missing_files
    
    def _verify_file_structure(self) -> bool:
        """Verify that the file structure is valid"""
        try:
            # Check if we have a reasonable directory structure
            has_directories = False
            has_files = False
            
            for root, dirs, files in os.walk(self.sandbox_dir):
                if dirs:
                    has_directories = True
                if files:
                    has_files = True
                
                # Check for suspicious patterns
                for file in files:
                    if file.startswith('.') and file not in ['.gitignore', '.env']:
                        self.logger.warning(f"Suspicious hidden file found: {file}")
            
            # Basic structure validation
            return has_files  # At minimum, we should have files
            
        except Exception as e:
            self.logger.error(f"File structure verification error: {str(e)}")
            return False
    
    def _check_file_corruption(self) -> List[str]:
        """Check for file corruption in restored files"""
        corruption_issues = []
        
        try:
            for root, dirs, files in os.walk(self.sandbox_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    try:
                        # Check file size
                        if os.path.getsize(file_path) == 0:
                            corruption_issues.append(f"Empty file: {file}")
                            continue
                        
                        # Try to read first few bytes of text files
                        if file.endswith(('.txt', '.html', '.css', '.js', '.json', '.md', '.py', '.sql')):
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    f.read(1024)  # Read first 1KB
                            except UnicodeDecodeError:
                                # This might be a binary file, which is fine
                                pass
                            except Exception as e:
                                corruption_issues.append(f"Corrupted text file: {file} ({str(e)})")
                        
                    except Exception as e:
                        corruption_issues.append(f"File access error: {file} ({str(e)})")
        
        except Exception as e:
            corruption_issues.append(f"Corruption check error: {str(e)}")
        
        return corruption_issues
    
    def get_verification_report(self, backup_file: str) -> Dict:
        """Get detailed verification report for a backup"""
        if not os.path.exists(backup_file):
            return {
                'error': 'Backup file not found',
                'file_exists': False
            }
        
        # Get file info
        file_info = {
            'file_exists': True,
            'file_size': os.path.getsize(backup_file),
            'file_modified': datetime.fromtimestamp(os.path.getmtime(backup_file)).isoformat(),
            'file_name': os.path.basename(backup_file)
        }
        
        # Check if encrypted
        is_encrypted = backup_file.endswith('.enc')
        file_info['encrypted'] = is_encrypted
        
        # Quick integrity check (without full verification)
        try:
            if is_encrypted:
                file_info['can_decrypt'] = True  # We'll assume yes for quick check
                file_info['integrity_status'] = 'Encrypted - requires decryption to verify'
            else:
                # Try to read ZIP file structure
                with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                    file_info['zip_files_count'] = len(zip_ref.namelist())
                    file_info['integrity_status'] = 'ZIP structure valid'
        except Exception as e:
            file_info['integrity_status'] = f'Invalid: {str(e)}'
        
        return file_info
    
    def cleanup_old_sandboxes(self, max_age_hours: int = 24):
        """Clean up old sandbox directories"""
        try:
            current_time = datetime.now().timestamp()
            
            # Clean up main sandbox if it's old
            if os.path.exists(self.sandbox_dir):
                sandbox_age = current_time - os.path.getmtime(self.sandbox_dir)
                if sandbox_age > (max_age_hours * 3600):
                    self._cleanup_sandbox()
                    self.logger.info(f"Cleaned up old sandbox directory: {self.sandbox_dir}")
            
            # Clean up any other sandbox directories
            sandbox_base = os.path.dirname(self.sandbox_dir)
            sandbox_name = os.path.basename(self.sandbox_dir)
            
            for item in os.listdir(sandbox_base):
                if item.startswith(sandbox_name) and item != sandbox_name:
                    item_path = os.path.join(sandbox_base, item)
                    if os.path.isdir(item_path):
                        item_age = current_time - os.path.getmtime(item_path)
                        if item_age > (max_age_hours * 3600):
                            shutil.rmtree(item_path)
                            self.logger.info(f"Cleaned up old sandbox: {item_path}")
        
        except Exception as e:
            self.logger.error(f"Error cleaning up old sandboxes: {str(e)}")
