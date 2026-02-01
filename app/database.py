import sqlite3
import json
from datetime import datetime
from typing import List, Optional
from app.models import BackupRecord, BackupCreate, BackupRecordExtended, AuditLog


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize SQLite database and create tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Backups table with Phase-3 enhancements
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                size INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'completed',
                checksum TEXT,
                encrypted INTEGER DEFAULT 0,
                backup_type TEXT DEFAULT 'full',
                app_name TEXT DEFAULT 'default',
                verified INTEGER DEFAULT 0,
                verification_status TEXT DEFAULT 'pending',
                snapshot_id TEXT,
                parent_backup_id INTEGER,
                FOREIGN KEY (parent_backup_id) REFERENCES backups (id)
            )
        ''')
        
        # Run automatic migration for missing columns
        self._migrate_backups_table(cursor)
        
        # Backup files tracking for incremental/differential
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS backup_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_id INTEGER NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_mtime REAL NOT NULL,
                file_hash TEXT NOT NULL,
                backup_type TEXT NOT NULL,
                FOREIGN KEY (backup_id) REFERENCES backups (id),
                UNIQUE(backup_id, file_path)
            )
        ''')
        
        # Applications table for multi-app support
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                source_path TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def _migrate_backups_table(self, cursor):
        """Automatically migrate backups table to add missing columns"""
        print("🔄 Starting database migration...")
        
        # Get existing columns
        cursor.execute("PRAGMA table_info(backups)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        print(f"📋 Existing columns: {existing_columns}")
        
        # Add missing columns if they don't exist
        migrations = [
            ("backup_type", "TEXT DEFAULT 'full'"),
            ("app_name", "TEXT DEFAULT 'default'"),
            ("verified", "INTEGER DEFAULT 0"),
            ("verification_status", "TEXT DEFAULT 'pending'"),
            ("snapshot_id", "TEXT"),
            ("encryption_enabled", "INTEGER DEFAULT 0")
        ]
        
        for column_name, column_def in migrations:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE backups ADD COLUMN {column_name} {column_def}")
                    print(f"✅ Added missing column: {column_name}")
                except sqlite3.Error as e:
                    print(f"⚠️  Could not add column {column_name}: {e}")
            else:
                print(f"✅ Column already exists: {column_name}")
        
        # Update existing records to have default values
        try:
            cursor.execute("UPDATE backups SET backup_type = 'full' WHERE backup_type IS NULL")
            cursor.execute("UPDATE backups SET app_name = 'default' WHERE app_name IS NULL")
            cursor.execute("UPDATE backups SET verified = 0 WHERE verified IS NULL")
            cursor.execute("UPDATE backups SET verification_status = 'pending' WHERE verification_status IS NULL")
            cursor.execute("UPDATE backups SET encryption_enabled = 0 WHERE encryption_enabled IS NULL")
            print("✅ Updated existing records with default values")
        except sqlite3.Error as e:
            print(f"⚠️  Could not update existing records: {e}")
        
        print("🎉 Database migration completed!")
    
    def create_backup_record(self, backup: BackupCreate, checksum: str = None, encrypted: bool = False, 
                          backup_type: str = 'full', app_name: str = 'default', parent_backup_id: int = None, 
                          snapshot_id: str = None) -> int:
        """Create a new backup record with Phase-3 enhancements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO backups (filename, size, created_at, status, checksum, encrypted, backup_type, app_name, verified, verification_status, snapshot_id, parent_backup_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 'pending', ?, ?)
        ''', (backup.filename, backup.size, datetime.now().isoformat(), backup.status, checksum, 
              1 if encrypted else 0, backup_type, app_name, snapshot_id, parent_backup_id))
        
        backup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return backup_id
    
    def get_all_backups(self) -> List[BackupRecordExtended]:
        """Get all backup records"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, filename, size, created_at, status, checksum, encrypted, backup_type, app_name, verified, verification_status, snapshot_id, parent_backup_id FROM backups ORDER BY created_at DESC')
        rows = cursor.fetchall()
        
        backups = []
        for row in rows:
            backups.append(BackupRecordExtended(
                id=row[0],
                filename=row[1],
                size=row[2],
                created_at=datetime.fromisoformat(row[3]),
                status=row[4],
                checksum=row[5],
                encrypted=bool(row[6]),
                backup_type=row[7],
                app_name=row[8],
                verified=bool(row[9]),
                verification_status=row[10],
                snapshot_id=row[11],
                parent_backup_id=row[12]
            ))
        
        conn.close()
        return backups
    
    def get_backup_by_id(self, backup_id: int) -> Optional[BackupRecordExtended]:
        """Get backup record by ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, filename, size, created_at, status, checksum, encrypted, backup_type, app_name, verified, parent_backup_id FROM backups WHERE id = ?', (backup_id,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return BackupRecordExtended(
                id=row[0],
                filename=row[1],
                size=row[2],
                created_at=datetime.fromisoformat(row[3]),
                status=row[4],
                checksum=row[5],
                encrypted=bool(row[6]),
                backup_type=row[7],
                app_name=row[8],
                verified=bool(row[9]),
                parent_backup_id=row[10]
            )
        return None
    
    # Phase-3 Database Methods
    
    def store_backup_files(self, backup_id: int, files_data: list, backup_type: str):
        """Store file metadata for incremental/differential tracking"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for file_info in files_data:
            cursor.execute('''
                INSERT OR REPLACE INTO backup_files (backup_id, file_path, file_size, file_mtime, file_hash, backup_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (backup_id, file_info['path'], file_info['size'], file_info['mtime'], file_info['hash'], backup_type))
        
        conn.commit()
        conn.close()
    
    def get_changed_files(self, backup_type: str, parent_backup_id: int = None, app_path: str = None) -> list:
        """Get changed files for incremental/differential backups"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if backup_type == 'incremental' and parent_backup_id:
            # Get files since last backup (any type)
            cursor.execute('''
                SELECT file_path, file_size, file_mtime, file_hash 
                FROM backup_files 
                WHERE backup_id = ? AND backup_type = 'full'
            ''', (parent_backup_id,))
        elif backup_type == 'differential' and parent_backup_id:
            # Get files since last full backup
            cursor.execute('''
                SELECT file_path, file_size, file_mtime, file_hash 
                FROM backup_files 
                WHERE backup_id = ? AND backup_type = 'full'
            ''', (parent_backup_id,))
        else:
            return []
        
        last_files = cursor.fetchall()
        conn.close()
        
        # Convert to dict for comparison
        last_files_dict = {row[0]: {'size': row[1], 'mtime': row[2], 'hash': row[3]} for row in last_files}
        
        # Get current files from filesystem
        import os
        import hashlib
        current_files = []
        
        if app_path and os.path.exists(app_path):
            for root, dirs, files in os.walk(app_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, app_path)
                    
                    try:
                        stat = os.stat(file_path)
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()
                        
                        current_files.append({
                            'path': rel_path,
                            'size': stat.st_size,
                            'mtime': stat.st_mtime,
                            'hash': file_hash
                        })
                    except (OSError, IOError):
                        continue
        
        # Find changed files
        changed_files = []
        for current_file in current_files:
            last_file = last_files_dict.get(current_file['path'])
            
            if not last_file:  # New file
                changed_files.append(current_file)
            elif (last_file['size'] != current_file['size'] or 
                  last_file['mtime'] != current_file['mtime'] or
                  last_file['hash'] != current_file['hash']):  # Modified file
                changed_files.append(current_file)
        
        return changed_files
    
    def get_latest_full_backup(self, app_name: str = 'default') -> Optional[int]:
        """Get the latest full backup ID for an application"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id FROM backups 
            WHERE backup_type = 'full' AND app_name = ? AND status = 'completed'
            ORDER BY created_at DESC LIMIT 1
        ''', (app_name,))
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def mark_backup_verified(self, backup_id: int, verified: bool = True):
        """Mark backup as verified or unverified"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE backups SET verified = ? WHERE id = ?
        ''', (1 if verified else 0, backup_id))
        
        conn.commit()
        conn.close()
    
    def create_application(self, name: str, source_path: str, description: str = None):
        """Create a new application record"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO applications (name, source_path, description, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, source_path, description, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def get_applications(self) -> list:
        """Get all active applications"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, source_path, description, created_at, is_active
            FROM applications WHERE is_active = 1
            ORDER BY name
        ''')
        
        apps = []
        for row in cursor.fetchall():
            apps.append({
                'id': row[0],
                'name': row[1],
                'source_path': row[2],
                'description': row[3],
                'created_at': row[4],
                'is_active': bool(row[5])
            })
        
        conn.close()
        return apps
    
    def get_application_by_name(self, name: str) -> Optional[dict]:
        """Get application by name"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, name, source_path, description, created_at, is_active
            FROM applications WHERE name = ? AND is_active = 1
        ''', (name,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row[0],
                'name': row[1],
                'source_path': row[2],
                'description': row[3],
                'created_at': row[4],
                'is_active': bool(row[5])
            }
        return None
