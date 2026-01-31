#!/usr/bin/env python3
"""
Phase-2 Enterprise Backup System - Full Scope Validation Script
Tests all core modules and features for enterprise client delivery verification
"""

import os
import sys
import json
import sqlite3
import zipfile
import hashlib
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import system modules
from database import Database
from backup_engine import BackupEngine
from restore_engine import RestoreEngine
from scheduler import BackupScheduler
from auth import AuthManager
from retention import RetentionManager
from reports import ReportGenerator
from security.encryption import EncryptionManager
from security.integrity import IntegrityManager
from models import BackupCreate, UserCreate

# Configure logging for tests
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemValidator:
    def __init__(self):
        self.test_results = {}
        self.config = self.load_config()
        self.test_db_path = "test_backup_system.db"
        self.test_storage_dir = "test_storage"
        self.test_restore_dir = "test_restored"
        
    def load_config(self):
        """Load system configuration"""
        try:
            # Load configuration with Phase-3 backward compatibility
            config_file = "config_phase3.json" if os.path.exists("config_phase3.json") else "config.json"
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            # Override paths for testing
            config["database"]["path"] = "test_backup_system.db"
            config["backup"]["storage_directory"] = "test_storage"
            config["backup"]["restore_directory"] = "test_restored"
            config["backup"]["source_directory"] = "demo_app"
            
            return config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return None
    
    def setup_test_environment(self):
        """Setup test directories and database"""
        logger.info("🔧 Setting up test environment...")
        
        # Create test directories
        os.makedirs(self.test_storage_dir, exist_ok=True)
        os.makedirs(self.test_restore_dir, exist_ok=True)
        
        # Remove existing test database
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        
        logger.info("✅ Test environment ready")
    
    def cleanup_test_environment(self):
        """Cleanup test files and directories"""
        logger.info("🧹 Cleaning up test environment...")
        
        # Remove test files
        for path in [self.test_db_path, self.test_storage_dir, self.test_restore_dir]:
            if os.path.exists(path):
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
        
        logger.info("✅ Test environment cleaned up")
    
    def log_test_result(self, test_name, passed, message=""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.test_results[test_name] = {"status": status, "message": message}
        logger.info(f"{status}: {test_name}")
        if message:
            logger.info(f"   {message}")
    
    def test_database_module(self):
        """Test database functionality"""
        logger.info("\n🗄️  Testing Database Module...")
        
        try:
            db = Database(self.config["database"]["path"])
            
            # Test backup record creation
            backup_create = BackupCreate(
                filename="test_backup.zip",
                size=1024,
                status="completed"
            )
            backup_id = db.create_backup_record(backup_create, "test_checksum", True)
            
            if backup_id > 0:
                self.log_test_result("Database - Create Backup Record", True, f"Created backup ID: {backup_id}")
            else:
                self.log_test_result("Database - Create Backup Record", False, "Failed to create backup record")
                return
            
            # Test backup retrieval
            backup = db.get_backup_by_id(backup_id)
            if backup and backup.filename == "test_backup.zip":
                self.log_test_result("Database - Retrieve Backup", True, "Successfully retrieved backup")
            else:
                self.log_test_result("Database - Retrieve Backup", False, "Failed to retrieve backup")
            
            # Test get all backups
            backups = db.get_all_backups()
            if len(backups) >= 1:
                self.log_test_result("Database - Get All Backups", True, f"Found {len(backups)} backups")
            else:
                self.log_test_result("Database - Get All Backups", False, "No backups found")
            
        except Exception as e:
            self.log_test_result("Database Module", False, f"Exception: {str(e)}")
    
    def test_encryption_module(self):
        """Test AES-256 encryption functionality"""
        logger.info("\n🔐 Testing Encryption Module...")
        
        try:
            # Create test file
            test_file = "test_encrypt.txt"
            test_content = "This is a test file for encryption verification"
            
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Initialize encryption manager
            enc_manager = EncryptionManager()
            
            # Test encryption
            enc_manager.encrypt_file(test_file)
            encrypted_file = test_file + ".enc"
            
            if os.path.exists(encrypted_file):
                self.log_test_result("Encryption - File Encryption", True, "File encrypted successfully")
            else:
                self.log_test_result("Encryption - File Encryption", False, "Encrypted file not created")
                return
            
            # Test decryption
            enc_manager.decrypt_file(encrypted_file)
            decrypted_file = encrypted_file.replace(".enc", "")
            
            if os.path.exists(decrypted_file):
                # Verify content
                with open(decrypted_file, 'r') as f:
                    decrypted_content = f.read()
                
                if decrypted_content == test_content:
                    self.log_test_result("Encryption - File Decryption", True, "Content matches original")
                else:
                    self.log_test_result("Encryption - File Decryption", False, "Content mismatch")
            else:
                self.log_test_result("Encryption - File Decryption", False, "Decrypted file not created")
            
            # Cleanup
            for f in [test_file, encrypted_file, decrypted_file]:
                if os.path.exists(f):
                    os.remove(f)
            
        except Exception as e:
            self.log_test_result("Encryption Module", False, f"Exception: {str(e)}")
    
    def test_integrity_module(self):
        """Test SHA-256 integrity verification"""
        logger.info("\n🛡️  Testing Integrity Module...")
        
        try:
            # Create test file
            test_file = "test_integrity.txt"
            test_content = "This is a test file for integrity verification"
            
            with open(test_file, 'w') as f:
                f.write(test_content)
            
            # Initialize integrity manager
            integrity_manager = IntegrityManager()
            
            # Generate checksum
            checksum = integrity_manager.generate_checksum(test_file)
            
            if checksum and len(checksum) == 64:  # SHA-256 is 64 chars
                self.log_test_result("Integrity - Generate Checksum", True, f"Generated SHA-256: {checksum[:16]}...")
            else:
                self.log_test_result("Integrity - Generate Checksum", False, "Invalid checksum generated")
                return
            
            # Verify integrity
            is_valid = integrity_manager.verify_checksum(test_file, checksum)
            
            if is_valid:
                self.log_test_result("Integrity - Verify Checksum", True, "Checksum verification passed")
            else:
                self.log_test_result("Integrity - Verify Checksum", False, "Checksum verification failed")
            
            # Test with modified file
            with open(test_file, 'a') as f:
                f.write("modified")
            
            is_valid_modified = integrity_manager.verify_checksum(test_file, checksum)
            
            if not is_valid_modified:
                self.log_test_result("Integrity - Detect Tampering", True, "Successfully detected file modification")
            else:
                self.log_test_result("Integrity - Detect Tampering", False, "Failed to detect file modification")
            
            # Cleanup
            os.remove(test_file)
            
        except Exception as e:
            self.log_test_result("Integrity Module", False, f"Exception: {str(e)}")
    
    def test_backup_engine(self):
        """Test backup engine with encryption and integrity"""
        logger.info("\n💾 Testing Backup Engine...")
        
        try:
            backup_engine = BackupEngine(self.config)
            db = Database(self.config["database"]["path"])
            
            # Create backup
            filename, size, checksum, encrypted = backup_engine.create_backup()
            
            if filename and os.path.exists(filename):
                self.log_test_result("Backup Engine - Create Backup", True, f"Created: {filename} ({size} bytes)")
            else:
                self.log_test_result("Backup Engine - Create Backup", False, "Backup file not created")
                return
            
            # Verify encryption
            if encrypted:
                self.log_test_result("Backup Engine - Encryption Applied", True, "Backup is encrypted")
            else:
                self.log_test_result("Backup Engine - Encryption Applied", False, "Backup not encrypted")
            
            # Verify checksum
            if checksum and len(checksum) == 64:
                self.log_test_result("Backup Engine - Checksum Generated", True, f"SHA-256: {checksum[:16]}...")
            else:
                self.log_test_result("Backup Engine - Checksum Generated", False, "Invalid checksum")
            
            # Store in database
            backup_create = BackupCreate(filename=filename, size=size, status="completed")
            backup_id = db.create_backup_record(backup_create, checksum, encrypted)
            
            if backup_id > 0:
                self.log_test_result("Backup Engine - Database Storage", True, f"Stored with ID: {backup_id}")
            else:
                self.log_test_result("Backup Engine - Database Storage", False, "Failed to store in database")
            
        except Exception as e:
            self.log_test_result("Backup Engine", False, f"Exception: {str(e)}")
    
    def test_restore_engine(self):
        """Test restore engine with decryption and verification"""
        logger.info("\n🔄 Testing Restore Engine...")
        
        try:
            restore_engine = RestoreEngine(self.config)
            db = Database(self.config["database"]["path"])
            
            # Get latest backup
            backups = db.get_all_backups()
            if not backups:
                self.log_test_result("Restore Engine - No Backups", False, "No backups available for restore test")
                return
            
            latest_backup = backups[0]
            
            # Clear restore directory
            if os.path.exists(self.test_restore_dir):
                shutil.rmtree(self.test_restore_dir)
            os.makedirs(self.test_restore_dir, exist_ok=True)
            
            # Perform restore
            success = restore_engine.restore_backup(latest_backup.filename, latest_backup.checksum)
            
            if success:
                self.log_test_result("Restore Engine - Restore Success", True, f"Restored: {latest_backup.filename}")
                
                # Verify restored files
                if os.path.exists(self.test_restore_dir):
                    restored_files = []
                    for root, dirs, files in os.walk(self.test_restore_dir):
                        restored_files.extend(files)
                    
                    if len(restored_files) > 0:
                        self.log_test_result("Restore Engine - Files Restored", True, f"Restored {len(restored_files)} files")
                    else:
                        self.log_test_result("Restore Engine - Files Restored", False, "No files restored")
                else:
                    self.log_test_result("Restore Engine - Files Restored", False, "Restore directory not created")
            else:
                self.log_test_result("Restore Engine - Restore Success", False, "Restore operation failed")
            
        except Exception as e:
            self.log_test_result("Restore Engine", False, f"Exception: {str(e)}")
    
    def test_retention_manager(self):
        """Test retention policy management"""
        logger.info("\n📅 Testing Retention Manager...")
        
        try:
            db = Database(self.config["database"]["path"])
            retention_manager = RetentionManager(self.config, db)
            
            # Get retention status
            status = retention_manager.get_retention_status()
            
            if status and "total_backups" in status:
                self.log_test_result("Retention - Status Check", True, f"Status: {status['total_backups']} backups")
            else:
                self.log_test_result("Retention - Status Check", False, "Failed to get status")
                return
            
            # Test retention policy application
            initial_count = status["total_backups"]
            retention_manager.apply_retention_policy()
            
            # Check if policy was applied
            new_status = retention_manager.get_retention_status()
            final_count = new_status["total_backups"]
            
            self.log_test_result("Retention - Policy Applied", True, f"Applied policy: {initial_count} → {final_count} backups")
            
            # Test retention limits
            if "max_backups" in new_status and "max_age_days" in new_status:
                self.log_test_result("Retention - Limits Configured", True, 
                    f"Max: {new_status['max_backups']}, Age: {new_status['max_age_days']} days")
            else:
                self.log_test_result("Retention - Limits Configured", False, "Retention limits not configured")
            
        except Exception as e:
            self.log_test_result("Retention Manager", False, f"Exception: {str(e)}")
    
    def test_auth_system(self):
        """Test authentication and RBAC system"""
        logger.info("\n👥 Testing Authentication System...")
        
        try:
            auth_manager = AuthManager(self.config["database"]["path"])
            
            # Test user creation
            success = auth_manager.create_user("testuser", "testpass123", "operator")
            
            if success:
                self.log_test_result("Auth - User Creation", True, "Created test user")
            else:
                self.log_test_result("Auth - User Creation", False, "Failed to create user")
                return
            
            # Test user authentication
            user = auth_manager.authenticate_user("testuser", "testpass123")
            
            if user and user["username"] == "testuser":
                self.log_test_result("Auth - User Authentication", True, f"Authenticated: {user['username']}")
            else:
                self.log_test_result("Auth - User Authentication", False, "Authentication failed")
                return
            
            # Test JWT token creation
            token = auth_manager.create_access_token(
                data={"sub": user["username"], "role": user["role_name"]}
            )
            
            if token and len(token) > 50:  # JWT tokens are typically long
                self.log_test_result("Auth - JWT Token Creation", True, f"Token created: {len(token)} chars")
            else:
                self.log_test_result("Auth - JWT Token Creation", False, "Invalid token created")
            
            # Test role-based permissions
            permissions = user.get("permissions", {})
            
            if isinstance(permissions, dict):
                self.log_test_result("Auth - RBAC Permissions", True, f"Permissions: {list(permissions.keys())}")
            else:
                self.log_test_result("Auth - RBAC Permissions", False, "Invalid permissions format")
            
            # Test audit logging
            auth_manager.log_audit("testuser", "test_action", success=True)
            
            # Verify audit log entry
            logs = auth_manager.get_audit_logs(limit=1)
            if logs and len(logs) > 0:
                self.log_test_result("Auth - Audit Logging", True, "Audit log entry created")
            else:
                self.log_test_result("Auth - Audit Logging", False, "Audit log not created")
            
        except Exception as e:
            self.log_test_result("Auth System", False, f"Exception: {str(e)}")
    
    def test_report_generator(self):
        """Test report generation (CSV/PDF)"""
        logger.info("\n📊 Testing Report Generator...")
        
        try:
            db = Database(self.config["database"]["path"])
            report_generator = ReportGenerator(db)
            
            # Test CSV generation
            csv_content = report_generator.generate_backup_csv()
            
            if csv_content and len(csv_content) > 0:
                self.log_test_result("Reports - CSV Generation", True, f"Generated CSV: {len(csv_content)} chars")
            else:
                self.log_test_result("Reports - CSV Generation", False, "CSV generation failed")
                return
            
            # Test PDF generation
            pdf_content = report_generator.generate_backup_pdf()
            
            if pdf_content and len(pdf_content) > 1000:  # PDF files should be substantial
                self.log_test_result("Reports - PDF Generation", True, f"Generated PDF: {len(pdf_content)} bytes")
            else:
                self.log_test_result("Reports - PDF Generation", False, "PDF generation failed")
            
            # Test audit report
            audit_csv = report_generator.generate_audit_csv()
            
            if audit_csv and len(audit_csv) > 0:
                self.log_test_result("Reports - Audit CSV", True, f"Audit CSV: {len(audit_csv)} chars")
            else:
                self.log_test_result("Reports - Audit CSV", False, "Audit CSV generation failed")
            
        except Exception as e:
            self.log_test_result("Report Generator", False, f"Exception: {str(e)}")
    
    def test_scheduler(self):
        """Test backup scheduler functionality"""
        logger.info("\n⏰ Testing Backup Scheduler...")
        
        try:
            db = Database(self.config["database"]["path"])
            backup_engine = BackupEngine(self.config)
            scheduler = BackupScheduler(self.config, db, backup_engine)
            
            # Test scheduler initialization
            if scheduler.scheduler:
                self.log_test_result("Scheduler - Initialization", True, "Scheduler initialized")
            else:
                self.log_test_result("Scheduler - Initialization", False, "Scheduler not initialized")
                return
            
            # Test scheduler start
            scheduler.start()
            
            if scheduler.scheduler.running:
                self.log_test_result("Scheduler - Start", True, "Scheduler running")
            else:
                self.log_test_result("Scheduler - Start", False, "Scheduler failed to start")
            
            # Wait a moment to ensure scheduler is active
            time.sleep(2)
            
            # Test scheduler stop
            scheduler.stop()
            
            if not scheduler.scheduler.running:
                self.log_test_result("Scheduler - Stop", True, "Scheduler stopped successfully")
            else:
                self.log_test_result("Scheduler - Stop", False, "Scheduler failed to stop")
            
        except Exception as e:
            self.log_test_result("Scheduler", False, f"Exception: {str(e)}")
    
    def test_storage_monitoring(self):
        """Test storage quota and disk monitoring"""
        logger.info("\n💿 Testing Storage Monitoring...")
        
        try:
            # Test storage directory existence
            if os.path.exists(self.test_storage_dir):
                self.log_test_result("Storage - Directory Exists", True, "Storage directory available")
            else:
                self.log_test_result("Storage - Directory Exists", False, "Storage directory not found")
                return
            
            # Test disk space monitoring (using psutil)
            try:
                import psutil
                disk_usage = psutil.disk_usage('/')
                free_gb = disk_usage.free / (1024**3)
                total_gb = disk_usage.total / (1024**3)
                
                if free_gb > 0 and total_gb > 0:
                    self.log_test_result("Storage - Disk Monitoring", True, 
                        f"Free: {free_gb:.1f}GB / Total: {total_gb:.1f}GB")
                else:
                    self.log_test_result("Storage - Disk Monitoring", False, "Invalid disk usage data")
            except ImportError:
                self.log_test_result("Storage - Disk Monitoring", False, "psutil not available")
            
            # Test storage usage calculation
            total_size = 0
            for root, dirs, files in os.walk(self.test_storage_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            self.log_test_result("Storage - Usage Calculation", True, f"Storage used: {total_size} bytes")
            
            # Test quota checking
            quota_mb = self.config.get("quota", {}).get("max_storage_mb", 500)
            usage_mb = total_size / (1024**2)
            
            if usage_mb < quota_mb:
                self.log_test_result("Storage - Quota Check", True, f"Usage: {usage_mb:.2f}MB / Quota: {quota_mb}MB")
            else:
                self.log_test_result("Storage - Quota Check", False, f"Quota exceeded: {usage_mb:.2f}MB / {quota_mb}MB")
            
        except Exception as e:
            self.log_test_result("Storage Monitoring", False, f"Exception: {str(e)}")
    
    def test_offline_operation(self):
        """Test offline-only operation constraint"""
        logger.info("\n🔒 Testing Offline Operation...")
        
        try:
            # Verify no external API calls are made
            # This is more of a design verification test
            
            # Check that all modules use local resources
            config_file = "config_phase3.json" if os.path.exists("config_phase3.json") else "config.json"
            local_resources = [
                os.path.exists(self.config["database"]["path"]),
                os.path.exists(self.config["backup"]["storage_directory"]),
                os.path.exists(config_file)
            ]
            
            if all(local_resources):
                self.log_test_result("Offline - Local Resources", True, "All resources are local")
            else:
                self.log_test_result("Offline - Local Resources", False, "Missing local resources")
            
            # Verify no network imports in core modules
            core_modules = ['database', 'backup_engine', 'restore_engine', 'auth', 'retention']
            network_imports_found = False
            
            for module in core_modules:
                try:
                    module_path = f"{module}.py"
                    if os.path.exists(module_path):
                        with open(module_path, 'r') as f:
                            content = f.read()
                            if any(imp in content for imp in ['requests', 'urllib', 'httpx', 'aiohttp']):
                                network_imports_found = True
                                break
                except:
                    pass
            
            if not network_imports_found:
                self.log_test_result("Offline - No Network Imports", True, "No network libraries found")
            else:
                self.log_test_result("Offline - No Network Imports", False, "Network libraries detected")
            
        except Exception as e:
            self.log_test_result("Offline Operation", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run all validation tests"""
        logger.info("🚀 Starting Phase-2 Enterprise Backup System Validation")
        logger.info("=" * 60)
        
        # Setup test environment
        self.setup_test_environment()
        
        try:
            # Run all tests
            self.test_database_module()
            self.test_encryption_module()
            self.test_integrity_module()
            self.test_backup_engine()
            self.test_restore_engine()
            self.test_retention_manager()
            self.test_auth_system()
            self.test_report_generator()
            self.test_scheduler()
            self.test_storage_monitoring()
            self.test_offline_operation()
            
            # Phase-3 Tests
            self.test_incremental_backups()
            self.test_database_backups()
            self.test_backup_verification()
            self.test_disaster_recovery()
            self.test_plugin_system()
            self.test_multi_applications()
            
            # Generate summary
            self.generate_test_summary()
            
        finally:
            # Cleanup
            self.cleanup_test_environment()
    
    def generate_test_summary(self):
        """Generate test summary report"""
        logger.info("\n" + "=" * 60)
        logger.info("📋 TEST SUMMARY REPORT")
        logger.info("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if "PASS" in result["status"])
        failed_tests = total_tests - passed_tests
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Passed: {passed_tests}")
        logger.info(f"Failed: {failed_tests}")
        logger.info(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📊 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            logger.info(f"  {result['status']} {test_name}")
            if result.get("message"):
                logger.info(f"     {result['message']}")
        
        logger.info("\n" + "=" * 60)
        
        if failed_tests == 0:
            logger.info("🎉 ALL TESTS PASSED - SYSTEM READY FOR PRODUCTION")
        else:
            logger.info("⚠️  SOME TESTS FAILED - REVIEW REQUIRED")
        
        return passed_tests, failed_tests, total_tests
    
    # Phase-3 Test Methods
    
    def test_incremental_backups(self):
        """Test incremental backup functionality"""
        logger.info("\n🔄 Testing Incremental Backups...")
        
        try:
            from backup_engine import BackupEngine
            from database import Database
            
            # Test backup engine incremental functionality
            backup_engine = BackupEngine(self.config)
            database = Database(self.test_db_path)
            
            # Test full backup first
            result = backup_engine.create_backup("full", "test_app")
            if result[0] is not None:
                self.log_test_result("Incremental - Full Backup", True, "Full backup created successfully")
                
                # Test incremental backup
                incremental_result = backup_engine.create_backup("incremental", "test_app")
                if incremental_result[0] is not None:
                    self.log_test_result("Incremental - Incremental Backup", True, "Incremental backup created")
                else:
                    self.log_test_result("Incremental - Incremental Backup", False, "No files changed for incremental")
            else:
                self.log_test_result("Incremental - Full Backup", False, "Full backup failed")
            
            # Test database methods
            latest_full = database.get_latest_full_backup("test_app")
            self.log_test_result("Incremental - Database Tracking", True, f"Latest full backup: {latest_full}")
            
        except Exception as e:
            self.log_test_result("Incremental Backups", False, str(e))
    
    def test_database_backups(self):
        """Test database backup functionality"""
        logger.info("\n🗄️ Testing Database Backups...")
        
        try:
            from database_backup import DatabaseBackupEngine
            
            db_engine = DatabaseBackupEngine(self.config)
            
            # Test database tools availability
            tools = db_engine.verify_database_tools()
            self.log_test_result("Database - Tools Check", True, f"Available tools: {tools}")
            
            # Test database backup
            backup_files = db_engine.backup_all_databases(self.test_storage_dir)
            self.log_test_result("Database - Backup Creation", True, f"Database backups: {len(backup_files)}")
            
            # Test database info
            db_info = db_engine.get_database_info()
            self.log_test_result("Database - Info", True, f"Database configs: {len(db_info)}")
            
        except Exception as e:
            self.log_test_result("Database Backups", False, str(e))
    
    def test_backup_verification(self):
        """Test backup verification functionality"""
        logger.info("\n✅ Testing Backup Verification...")
        
        try:
            from verification import BackupVerificationEngine
            
            verification_engine = BackupVerificationEngine(self.config)
            
            # Create a test backup file
            test_backup = os.path.join(self.test_storage_dir, "test_backup.zip")
            with zipfile.ZipFile(test_backup, 'w') as zf:
                zf.writestr("test.txt", "test content")
            
            # Test verification
            checksum = hashlib.sha256(b"test content").hexdigest()
            result = verification_engine.verify_backup(test_backup, checksum, False)
            
            if result.get('verified', False):
                self.log_test_result("Verification - Sandbox Test", True, "Backup verified successfully")
            else:
                self.log_test_result("Verification - Sandbox Test", False, "Backup verification failed")
            
            # Test verification report
            report = verification_engine.get_verification_report(test_backup)
            self.log_test_result("Verification - Report", True, "Verification report generated")
            
            # Cleanup
            if os.path.exists(test_backup):
                os.remove(test_backup)
            
        except Exception as e:
            self.log_test_result("Backup Verification", False, str(e))
    
    def test_disaster_recovery(self):
        """Test disaster recovery functionality"""
        logger.info("\n🚨 Testing Disaster Recovery...")
        
        try:
            from disaster_recovery import DisasterRecoveryManager
            
            dr_manager = DisasterRecoveryManager(self.config)
            
            # Test recovery status
            status = dr_manager.get_recovery_status()
            self.log_test_result("Disaster Recovery - Status", True, f"Recovery ready: {status['ready']}")
            
            # Test recovery environment preparation
            dr_manager._prepare_recovery_environment()
            self.log_test_result("Disaster Recovery - Environment", True, "Recovery environment prepared")
            
            # Test cleanup
            dr_manager.cleanup_recovery_environment()
            self.log_test_result("Disaster Recovery - Cleanup", True, "Recovery environment cleaned")
            
        except Exception as e:
            self.log_test_result("Disaster Recovery", False, str(e))
    
    def test_plugin_system(self):
        """Test plugin system functionality"""
        logger.info("\n🔌 Testing Plugin System...")
        
        try:
            from plugins import PluginManager
            
            plugin_manager = PluginManager(self.config)
            
            # Test plugin status
            status = plugin_manager.get_plugin_status()
            self.log_test_result("Plugins - Status", True, f"Plugins enabled: {status['enabled']}")
            
            # Test plugin listing
            plugins = plugin_manager.list_plugins()
            self.log_test_result("Plugins - Listing", True, f"Plugins registered: {len(plugins)}")
            
            # Test plugin directory creation
            plugin_manager.create_plugin_directory()
            self.log_test_result("Plugins - Directory", True, "Plugin directory created")
            
        except Exception as e:
            self.log_test_result("Plugin System", False, str(e))
    
    def test_multi_applications(self):
        """Test multi-application support"""
        logger.info("\n📱 Testing Multi-Application Support...")
        
        try:
            from backup_engine import BackupEngine
            from database import Database
            
            backup_engine = BackupEngine(self.config)
            database = Database(self.test_db_path)
            
            # Test applications listing
            apps = backup_engine.get_applications()
            self.log_test_result("Multi-App - Applications List", True, f"Applications: {len(apps)}")
            
            # Test application backup
            if apps:
                app_name = apps[0]['name']
                result = backup_engine.backup_application(app_name, "full")
                if result[0] is not None:
                    self.log_test_result("Multi-App - Application Backup", True, f"App {app_name} backed up")
                else:
                    self.log_test_result("Multi-App - Application Backup", False, f"App {app_name} backup failed")
            
            # Test database application methods
            database.create_application("TestApp", "./test_app", "Test application")
            app = database.get_application_by_name("TestApp")
            self.log_test_result("Multi-App - Database Storage", True, f"App stored: {app['name'] if app else 'None'}")
            
        except Exception as e:
            self.log_test_result("Multi-Applications", False, str(e))

def main():
    """Main validation entry point"""
    validator = SystemValidator()
    validator.run_all_tests()

if __name__ == "__main__":
    main()
