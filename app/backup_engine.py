import os
import zipfile
import logging
import hashlib
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from app.security.encryption import EncryptionManager
from app.security.integrity import IntegrityManager
from app.database_backup import DatabaseBackupEngine


class BackupEngine:
    def __init__(self, config: dict):
        self.source_dir = config["backup"]["source_directory"]
        self.storage_dir = config["backup"]["storage_directory"]
        self.compression_level = config["backup"]["compression_level"]
        self.encryption_enabled = config["backup"].get("encryption_enabled", False)
        self.default_backup_type = config["backup"].get("default_backup_type", "full")
        self.config = config
        self.setup_logging()
        
        if self.encryption_enabled:
            key_file = config["security"]["encryption_key_file"]
            self.encryption_manager = EncryptionManager(key_file)
            self.integrity_manager = IntegrityManager()
        
        # Initialize database backup engine
        self.db_backup_engine = DatabaseBackupEngine(config)
        
        # Database access for file tracking
        from app.database import Database
        self.database = Database(config["database"]["path"])
        
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_type: str = "full", app_name: str = "default", parent_backup_id: int = None) -> Tuple[str, int, str, bool]:
        """
        Create a backup of the source directory with Phase-3 enhancements
        Returns: (backup_filename, backup_size, checksum, encrypted)
        """
        try:
            # Ensure storage directory exists
            os.makedirs(self.storage_dir, exist_ok=True)
            
            # Generate backup filename with timestamp and type
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_{backup_type}_{app_name}_{timestamp}.zip"
            backup_path = os.path.join(self.storage_dir, backup_filename)
            
            self.logger.info(f"Creating {backup_type} backup: {backup_filename}")
            
            # Get files to backup based on type
            files_to_backup = self._get_files_to_backup(backup_type, app_name, parent_backup_id)
            
            if not files_to_backup and backup_type != "full":
                self.logger.info(f"No files to backup for {backup_type} backup")
                return None, 0, None, False
            
            # Create backup record in database
            from app.models import BackupCreate
            backup_create = BackupCreate(filename=backup_filename, size=0, status="in_progress")
            backup_id = self.database.create_backup_record(
                backup_create, 
                encrypted=self.encryption_enabled,
                backup_type=backup_type,
                app_name=app_name,
                parent_backup_id=parent_backup_id
            )
            
            # Create ZIP archive
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=self.compression_level) as zipf:
                # Backup application files
                for file_info in files_to_backup:
                    file_path = file_info['path']
                    if os.path.exists(file_path):
                        arcname = os.path.relpath(file_path, start=os.path.dirname(self.source_dir))
                        zipf.write(file_path, arcname)
                
                # Backup databases if configured
                db_backup_files = self.db_backup_engine.backup_all_databases(self.storage_dir)
                for db_file in db_backup_files:
                    if os.path.exists(db_file):
                        arcname = os.path.relpath(db_file, start=self.storage_dir)
                        zipf.write(db_file, f"databases/{arcname}")
                        # Clean up temporary database backup files
                        os.remove(db_file)
            
            # Get backup size
            backup_size = os.path.getsize(backup_path)
            
            # Encrypt if enabled
            if self.encryption_enabled:
                encrypted_path = backup_path + ".enc"
                if self.encryption_manager.encrypt_file(backup_path, encrypted_path):
                    # Remove unencrypted file
                    os.remove(backup_path)
                    backup_filename = backup_filename + ".enc"
                    backup_size = os.path.getsize(encrypted_path)
                    self.logger.info(f"Backup encrypted: {backup_filename}")
                    
                    # Calculate checksum AFTER encryption (Option A - Preferred)
                    checksum = self.integrity_manager.generate_checksum(encrypted_path)
                else:
                    raise Exception("Encryption failed")
            else:
                # Calculate checksum for unencrypted backup
                checksum = self.integrity_manager.generate_checksum(backup_path) if self.integrity_manager else None
            
            # Store file metadata in database
            self.database.store_backup_files(backup_id, files_to_backup, backup_type)
            
            # Update backup record with final size
            self.logger.info(f"{backup_type.capitalize()} backup created successfully: {backup_filename} ({backup_size} bytes)")
            return backup_filename, backup_size, checksum, self.encryption_enabled
            
        except Exception as e:
            self.logger.error(f"Backup creation failed: {str(e)}")
            raise
    
    def _get_files_to_backup(self, backup_type: str, app_name: str = "default", parent_backup_id: int = None) -> List[Dict]:
        """Get list of files to backup based on backup type"""
        files_to_backup = []
        
        if backup_type == "full":
            # Full backup - include all files
            for root, dirs, files in os.walk(self.source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        stat = os.stat(file_path)
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        files_to_backup.append({
                            'path': file_path,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime,
                            'hash': file_hash
                        })
                    except (OSError, IOError):
                        continue
        
        elif backup_type in ["incremental", "differential"]:
            # Get parent backup for incremental/differential
            if not parent_backup_id:
                parent_backup_id = self.database.get_latest_full_backup(app_name)
                if not parent_backup_id:
                    self.logger.warning(f"No full backup found for {app_name}, falling back to full backup")
                    return self._get_files_to_backup("full", app_name)
            
            # Get changed files using database
            app_source = self._get_app_source_path(app_name)
            changed_files = self.database.get_changed_files(backup_type, parent_backup_id, app_source)
            
            if not changed_files:
                self.logger.info(f"No changes detected for {backup_type} backup")
                return []
            
            self.logger.info(f"Found {len(changed_files)} changed files for {backup_type} backup")
            return changed_files
        
        return files_to_backup
    
    def _get_app_source_path(self, app_name: str) -> str:
        """Get source path for an application"""
        applications = self.get_applications()
        for app in applications:
            if app["name"] == app_name:
                return app["source"]
        return self.source_dir  # Fallback to default
    
    def get_applications(self) -> List[Dict]:
        """Get list of configured applications"""
        applications = self.config.get("applications", [])
        if not applications:
            # Fallback to default application
            applications = [{"name": "default", "source": self.source_dir, "description": "Default application"}]
        return applications
    
    def backup_application(self, app_name: str, backup_type: str = "full") -> Tuple[str, int, str, bool]:
        """Backup a specific application"""
        applications = self.get_applications()
        
        # Find application by name
        app_config = None
        for app in applications:
            if app["name"] == app_name:
                app_config = app
                break
        
        if not app_config:
            raise ValueError(f"Application '{app_name}' not found in configuration")
        
        # Temporarily update source directory
        original_source = self.source_dir
        self.source_dir = app_config["source"]
        
        try:
            return self.create_backup(backup_type, app_name)
        finally:
            # Restore original source directory
            self.source_dir = original_source
