import os
import logging
from datetime import datetime, timedelta
from typing import List
from database import Database
from models import BackupRecord


class RetentionManager:
    def __init__(self, config: dict, database: Database):
        self.config = config
        self.database = database
        self.storage_dir = config["backup"]["storage_directory"]
        self.max_backups = config.get("retention", {}).get("max_backups", 10)
        self.max_age_days = config.get("retention", {}).get("max_age_days", 30)
        self.logger = logging.getLogger(__name__)
    
    def apply_retention_policy(self) -> dict:
        """
        Apply retention policy to clean up old backups
        Returns: dict with cleanup results
        """
        try:
            self.logger.info("Starting retention policy cleanup")
            
            backups = self.database.get_all_backups()
            cleanup_results = {
                "deleted_count": 0,
                "deleted_files": [],
                "errors": []
            }
            
            # Get current time for age calculations
            now = datetime.now()
            max_age_date = now - timedelta(days=self.max_age_days)
            
            # Identify backups to delete
            backups_to_delete = []
            
            for i, backup in enumerate(backups):
                should_delete = False
                reason = ""
                
                # Check age-based retention
                if backup.created_at < max_age_date:
                    should_delete = True
                    reason = f"Older than {self.max_age_days} days"
                
                # Check count-based retention (keep only N most recent)
                if i >= self.max_backups:
                    should_delete = True
                    reason = f"Exceeds maximum backup count of {self.max_backups}"
                
                if should_delete:
                    backups_to_delete.append({
                        "backup": backup,
                        "reason": reason
                    })
            
            # Delete identified backups
            for item in backups_to_delete:
                backup = item["backup"]
                reason = item["reason"]
                
                try:
                    # Delete encrypted file if exists
                    encrypted_file = os.path.join(self.storage_dir, backup.filename + ".enc")
                    if os.path.exists(encrypted_file):
                        os.remove(encrypted_file)
                        self.logger.info(f"Deleted encrypted file: {encrypted_file}")
                    
                    # Delete unencrypted file if exists
                    unencrypted_file = os.path.join(self.storage_dir, backup.filename)
                    if os.path.exists(unencrypted_file):
                        os.remove(unencrypted_file)
                        self.logger.info(f"Deleted unencrypted file: {unencrypted_file}")
                    
                    # Delete from database
                    self._delete_backup_record(backup.id)
                    
                    cleanup_results["deleted_count"] += 1
                    cleanup_results["deleted_files"].append({
                        "id": backup.id,
                        "filename": backup.filename,
                        "reason": reason,
                        "created_at": backup.created_at.isoformat()
                    })
                    
                    self.logger.info(f"Deleted backup ID {backup.id}: {backup.filename} ({reason})")
                    
                except Exception as e:
                    error_msg = f"Failed to delete backup ID {backup.id}: {str(e)}"
                    cleanup_results["errors"].append(error_msg)
                    self.logger.error(error_msg)
            
            self.logger.info(f"Retention cleanup completed. Deleted {cleanup_results['deleted_count']} backups")
            
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Retention policy application failed: {str(e)}")
            return {
                "deleted_count": 0,
                "deleted_files": [],
                "errors": [str(e)]
            }
    
    def _delete_backup_record(self, backup_id: int) -> bool:
        """Delete backup record from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.config["database"]["path"])
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM backups WHERE id = ?", (backup_id,))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete backup record ID {backup_id}: {str(e)}")
            return False
    
    def get_retention_status(self) -> dict:
        """Get current retention status and statistics"""
        try:
            backups = self.database.get_all_backups()
            now = datetime.now()
            max_age_date = now - timedelta(days=self.max_age_days)
            
            total_backups = len(backups)
            old_backups = len([b for b in backups if b.created_at < max_age_date])
            excess_backups = max(0, total_backups - self.max_backups)
            
            # Calculate storage usage
            total_size = 0
            for backup in backups:
                backup_file = os.path.join(self.storage_dir, backup.filename + ".enc")
                if os.path.exists(backup_file):
                    total_size += os.path.getsize(backup_file)
                else:
                    backup_file = os.path.join(self.storage_dir, backup.filename)
                    if os.path.exists(backup_file):
                        total_size += os.path.getsize(backup_file)
            
            return {
                "total_backups": total_backups,
                "old_backups": old_backups,
                "excess_backups": excess_backups,
                "max_backups": self.max_backups,
                "max_age_days": self.max_age_days,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get retention status: {str(e)}")
            return {
                "total_backups": 0,
                "old_backups": 0,
                "excess_backups": 0,
                "max_backups": self.max_backups,
                "max_age_days": self.max_age_days,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
