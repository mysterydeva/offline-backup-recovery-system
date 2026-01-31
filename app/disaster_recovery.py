"""
Disaster Recovery Module - Phase-3 Enhancement
Provides complete environment rebuild capabilities
"""

import os
import shutil
import zipfile
import logging
from datetime import datetime
from typing import Dict, Optional, List
from database import Database
from restore_engine import RestoreEngine
from verification import BackupVerificationEngine
from security.encryption import EncryptionManager
from security.integrity import IntegrityManager


class DisasterRecoveryManager:
    """Disaster recovery manager for complete environment rebuild"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.database = Database(config['database']['path'])
        self.restore_engine = RestoreEngine(config)
        self.verification_engine = BackupVerificationEngine(config)
        self.encryption_manager = EncryptionManager()
        self.integrity_manager = IntegrityManager()
        
        # Recovery configuration
        self.recovery_config = config.get('disaster_recovery', {})
        self.recovery_target = self.recovery_config.get('recovery_directory', 'disaster_recovery')
        self.auto_verify = self.recovery_config.get('auto_verify', True)
        self.backup_configs = self.recovery_config.get('restore_configs', True)
    
    def perform_disaster_recovery(self, app_name: str = 'default') -> Dict:
        """
        Perform complete disaster recovery
        
        Args:
            app_name: Application name to recover
            
        Returns:
            Dict with recovery result
        """
        recovery_result = {
            'success': False,
            'timestamp': datetime.now().isoformat(),
            'app_name': app_name,
            'steps_completed': [],
            'errors': [],
            'warnings': [],
            'files_restored': 0,
            'configs_restored': 0,
            'databases_restored': 0,
            'verification_passed': False
        }
        
        try:
            self.logger.info(f"Starting disaster recovery for application: {app_name}")
            
            # Step 1: Find latest verified backup
            backup_info = self._find_latest_verified_backup(app_name)
            if not backup_info:
                recovery_result['errors'].append("No verified backup found for disaster recovery")
                self.logger.error("Disaster recovery failed: No verified backup available")
                return recovery_result
            
            recovery_result['steps_completed'].append(f"Found verified backup: {backup_info['filename']}")
            self.logger.info(f"Using backup for recovery: {backup_info['filename']}")
            
            # Step 2: Prepare recovery environment
            self._prepare_recovery_environment()
            recovery_result['steps_completed'].append("Recovery environment prepared")
            
            # Step 3: Restore files
            restore_result = self._restore_files(backup_info, app_name)
            if not restore_result['success']:
                recovery_result['errors'].extend(restore_result['errors'])
                self.logger.error("File restoration failed during disaster recovery")
                return recovery_result
            
            recovery_result['files_restored'] = restore_result['files_restored']
            recovery_result['steps_completed'].append(f"Files restored: {restore_result['files_restored']}")
            
            # Step 4: Restore configurations
            if self.backup_configs:
                config_result = self._restore_configurations()
                recovery_result['configs_restored'] = config_result['configs_restored']
                recovery_result['steps_completed'].append(f"Configurations restored: {config_result['configs_restored']}")
                
                if config_result['warnings']:
                    recovery_result['warnings'].extend(config_result['warnings'])
            
            # Step 5: Restore databases
            db_result = self._restore_databases()
            recovery_result['databases_restored'] = db_result['databases_restored']
            recovery_result['steps_completed'].append(f"Databases restored: {db_result['databases_restored']}")
            
            if db_result['warnings']:
                recovery_result['warnings'].extend(db_result['warnings'])
            
            # Step 6: Verify recovery
            if self.auto_verify:
                verification_result = self._verify_recovery(app_name)
                recovery_result['verification_passed'] = verification_result['success']
                recovery_result['steps_completed'].append("Recovery verification completed")
                
                if not verification_result['success']:
                    recovery_result['errors'].extend(verification_result['errors'])
                    self.logger.error("Recovery verification failed")
                    return recovery_result
            
            # Step 7: Generate recovery report
            self._generate_recovery_report(recovery_result)
            recovery_result['steps_completed'].append("Recovery report generated")
            
            # Success!
            recovery_result['success'] = True
            self.logger.info(f"Disaster recovery completed successfully for {app_name}")
            
        except Exception as e:
            recovery_result['errors'].append(f"Disaster recovery error: {str(e)}")
            self.logger.error(f"Disaster recovery failed: {str(e)}")
        
        return recovery_result
    
    def _find_latest_verified_backup(self, app_name: str) -> Optional[Dict]:
        """Find the latest verified backup for an application"""
        try:
            backups = self.database.get_all_backups()
            
            # Filter by app name and verified status
            verified_backups = [
                backup for backup in backups 
                if backup.app_name == app_name and backup.verified and backup.status == 'completed'
            ]
            
            if not verified_backups:
                return None
            
            # Sort by creation date (newest first)
            latest_backup = max(verified_backups, key=lambda b: b.created_at)
            
            return {
                'id': latest_backup.id,
                'filename': latest_backup.filename,
                'created_at': latest_backup.created_at,
                'backup_type': latest_backup.backup_type,
                'checksum': latest_backup.checksum,
                'encrypted': latest_backup.encrypted
            }
        
        except Exception as e:
            self.logger.error(f"Error finding verified backup: {str(e)}")
            return None
    
    def _prepare_recovery_environment(self):
        """Prepare the disaster recovery environment"""
        try:
            # Clean up existing recovery directory
            if os.path.exists(self.recovery_target):
                shutil.rmtree(self.recovery_target)
            
            # Create fresh recovery directory
            os.makedirs(self.recovery_target, exist_ok=True)
            
            # Create subdirectories
            subdirs = ['restored_files', 'configs', 'databases', 'logs', 'reports']
            for subdir in subdirs:
                os.makedirs(os.path.join(self.recovery_target, subdir), exist_ok=True)
            
            self.logger.info(f"Recovery environment prepared: {self.recovery_target}")
        
        except Exception as e:
            self.logger.error(f"Failed to prepare recovery environment: {str(e)}")
            raise
    
    def _restore_files(self, backup_info: Dict, app_name: str) -> Dict:
        """Restore files from backup"""
        result = {
            'success': False,
            'files_restored': 0,
            'errors': []
        }
        
        try:
            backup_file = backup_info['filename']
            restore_path = os.path.join(self.recovery_target, 'restored_files')
            
            # Use restore engine to restore files
            success = self.restore_engine.restore_backup(
                backup_file, 
                backup_info['checksum'], 
                restore_path
            )
            
            if success:
                # Count restored files
                files_count = 0
                for root, dirs, files in os.walk(restore_path):
                    files_count += len(files)
                
                result['success'] = True
                result['files_restored'] = files_count
                self.logger.info(f"Files restored successfully: {files_count} files")
            else:
                result['errors'].append("File restoration failed")
        
        except Exception as e:
            result['errors'].append(f"File restoration error: {str(e)}")
            self.logger.error(f"File restoration error: {str(e)}")
        
        return result
    
    def _restore_configurations(self) -> Dict:
        """Restore configuration files"""
        result = {
            'configs_restored': 0,
            'warnings': []
        }
        
        try:
            config_dir = os.path.join(self.recovery_target, 'restored_files')
            target_config_dir = os.path.join(self.recovery_target, 'configs')
            
            # Look for configuration files
            config_files = ['config.json', '.env', 'requirements.txt', 'settings.py']
            
            for config_file in config_files:
                source_path = os.path.join(config_dir, config_file)
                if os.path.exists(source_path):
                    target_path = os.path.join(target_config_dir, config_file)
                    shutil.copy2(source_path, target_path)
                    result['configs_restored'] += 1
                    self.logger.info(f"Configuration restored: {config_file}")
                else:
                    result['warnings'].append(f"Configuration file not found: {config_file}")
        
        except Exception as e:
            self.logger.error(f"Configuration restoration error: {str(e)}")
            result['warnings'].append(f"Configuration restoration error: {str(e)}")
        
        return result
    
    def _restore_databases(self) -> Dict:
        """Restore databases from backup"""
        result = {
            'databases_restored': 0,
            'warnings': []
        }
        
        try:
            # Look for database backup files
            restored_files_dir = os.path.join(self.recovery_target, 'restored_files')
            target_db_dir = os.path.join(self.recovery_target, 'databases')
            
            # Find database backup files
            db_extensions = ['.sql', '.db', '.sqlite', '.sqlite3', '.dump']
            
            for root, dirs, files in os.walk(restored_files_dir):
                for file in files:
                    if any(file.endswith(ext) for ext in db_extensions):
                        source_path = os.path.join(root, file)
                        target_path = os.path.join(target_db_dir, file)
                        
                        # Create subdirectories if needed
                        os.makedirs(os.path.dirname(target_path), exist_ok=True)
                        shutil.copy2(source_path, target_path)
                        result['databases_restored'] += 1
                        self.logger.info(f"Database backup restored: {file}")
        
        except Exception as e:
            self.logger.error(f"Database restoration error: {str(e)}")
            result['warnings'].append(f"Database restoration error: {str(e)}")
        
        return result
    
    def _verify_recovery(self, app_name: str) -> Dict:
        """Verify that recovery was successful"""
        result = {
            'success': False,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Verify restored files exist
            restored_files_dir = os.path.join(self.recovery_target, 'restored_files')
            
            if not os.path.exists(restored_files_dir):
                result['errors'].append("Restored files directory not found")
                return result
            
            # Count files
            file_count = 0
            for root, dirs, files in os.walk(restored_files_dir):
                file_count += len(files)
            
            if file_count == 0:
                result['errors'].append("No files were restored")
                return result
            
            # Verify key files exist
            key_files = ['config.json', 'README.md']
            for key_file in key_files:
                file_path = os.path.join(restored_files_dir, key_file)
                if not os.path.exists(file_path):
                    result['warnings'].append(f"Key file missing: {key_file}")
            
            # Verify configurations
            config_dir = os.path.join(self.recovery_target, 'configs')
            if os.path.exists(config_dir):
                config_files = os.listdir(config_dir)
                if not config_files:
                    result['warnings'].append("No configuration files restored")
            
            # Verify databases
            db_dir = os.path.join(self.recovery_target, 'databases')
            if os.path.exists(db_dir):
                db_files = os.listdir(db_dir)
                if not db_files:
                    result['warnings'].append("No database files restored")
            
            result['success'] = True
            self.logger.info(f"Recovery verification passed: {file_count} files restored")
        
        except Exception as e:
            result['errors'].append(f"Recovery verification error: {str(e)}")
            self.logger.error(f"Recovery verification error: {str(e)}")
        
        return result
    
    def _generate_recovery_report(self, recovery_result: Dict):
        """Generate a detailed recovery report"""
        try:
            report_dir = os.path.join(self.recovery_target, 'reports')
            os.makedirs(report_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = os.path.join(report_dir, f"recovery_report_{timestamp}.txt")
            
            with open(report_file, 'w') as f:
                f.write("DISASTER RECOVERY REPORT\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Recovery Timestamp: {recovery_result['timestamp']}\n")
                f.write(f"Application: {recovery_result['app_name']}\n")
                f.write(f"Success: {'YES' if recovery_result['success'] else 'NO'}\n\n")
                
                f.write("STEPS COMPLETED:\n")
                f.write("-" * 20 + "\n")
                for step in recovery_result['steps_completed']:
                    f.write(f"✓ {step}\n")
                
                f.write(f"\nFILES RESTORED: {recovery_result['files_restored']}\n")
                f.write(f"CONFIGURATIONS RESTORED: {recovery_result['configs_restored']}\n")
                f.write(f"DATABASES RESTORED: {recovery_result['databases_restored']}\n")
                f.write(f"VERIFICATION PASSED: {'YES' if recovery_result['verification_passed'] else 'NO'}\n")
                
                if recovery_result['errors']:
                    f.write("\nERRORS:\n")
                    f.write("-" * 20 + "\n")
                    for error in recovery_result['errors']:
                        f.write(f"✗ {error}\n")
                
                if recovery_result['warnings']:
                    f.write("\nWARNINGS:\n")
                    f.write("-" * 20 + "\n")
                    for warning in recovery_result['warnings']:
                        f.write(f"⚠ {warning}\n")
            
            self.logger.info(f"Recovery report generated: {report_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to generate recovery report: {str(e)}")
    
    def get_recovery_status(self) -> Dict:
        """Get current disaster recovery status"""
        status = {
            'ready': True,
            'verified_backups': 0,
            'last_recovery': None,
            'recovery_environment': {
                'exists': os.path.exists(self.recovery_target),
                'size': self._get_directory_size(self.recovery_target) if os.path.exists(self.recovery_target) else 0
            },
            'capabilities': {
                'auto_verify': self.auto_verify,
                'restore_configs': self.backup_configs
            }
        }
        
        try:
            # Count verified backups
            backups = self.database.get_all_backups()
            status['verified_backups'] = len([b for b in backups if b.verified])
            
            # Check if we have any verified backups
            if status['verified_backups'] == 0:
                status['ready'] = False
            
        except Exception as e:
            self.logger.error(f"Error getting recovery status: {str(e)}")
            status['ready'] = False
        
        return status
    
    def _get_directory_size(self, path: str) -> int:
        """Get total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception:
            pass
        return total_size
    
    def cleanup_recovery_environment(self):
        """Clean up the disaster recovery environment"""
        try:
            if os.path.exists(self.recovery_target):
                shutil.rmtree(self.recovery_target)
                self.logger.info(f"Disaster recovery environment cleaned up: {self.recovery_target}")
        except Exception as e:
            self.logger.error(f"Failed to cleanup recovery environment: {str(e)}")
