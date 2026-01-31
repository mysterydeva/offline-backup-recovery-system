import bcrypt
import jwt
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import logging
import json


security = HTTPBearer()
SECRET_KEY = "your-secret-key-change-in-production"  # In production, use environment variable
ALGORITHM = "HS256"


class AuthManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self):
        """Initialize user authentication tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create roles table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                permissions TEXT NOT NULL
            )
        ''')
        
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (role_id) REFERENCES roles (id)
            )
        ''')
        
        # Create audit_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT,
                timestamp TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                success INTEGER DEFAULT 1
            )
        ''')
        
        # Insert default roles if they don't exist
        cursor.execute("SELECT COUNT(*) FROM roles WHERE name = 'admin'")
        if cursor.fetchone()[0] == 0:
            cursor.executemany('''
                INSERT INTO roles (name, permissions) VALUES (?, ?)
            ''', [
                ('admin', json.dumps({"backup": True, "restore": True, "manage_users": True, "view": True, "export": True})),
                ('operator', json.dumps({"backup": True, "restore": True, "view": True, "export": False})),
                ('viewer', json.dumps({"backup": False, "restore": False, "view": True, "export": False}))
            ])
        
        # Create default admin user if no users exist
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            default_password = self.hash_password("admin123")
            cursor.execute('''
                INSERT INTO users (username, password_hash, role_id, created_at)
                VALUES (?, ?, (SELECT id FROM roles WHERE name = 'admin'), ?)
            ''', ("admin", default_password, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user and return user data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, u.password_hash, u.role_id, r.name as role_name, r.permissions, u.is_active
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
            ''', (username,))
            
            user_data = cursor.fetchone()
            conn.close()
            
            if user_data and user_data[6] == 1:  # is_active
                user_id, username, password_hash, role_id, role_name, permissions, is_active = user_data
                
                if self.verify_password(password, password_hash):
                    # Update last login
                    self.update_last_login(user_id)
                    
                    return {
                        "id": user_id,
                        "username": username,
                        "role_id": role_id,
                        "role_name": role_name,
                        "permissions": json.loads(permissions)
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None
    
    def update_last_login(self, user_id: int):
        """Update user's last login timestamp"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", 
                          (datetime.now().isoformat(), user_id))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to update last login: {str(e)}")
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=24)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.PyJWTError:
            return None
    
    def log_audit(self, username: str, action: str, resource: str = None, 
                  success: bool = True, ip_address: str = None, user_agent: str = None):
        """Log audit entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO audit_logs (username, action, resource, timestamp, ip_address, user_agent, success)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, action, resource, datetime.now().isoformat(), 
                  ip_address, user_agent, 1 if success else 0))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to log audit: {str(e)}")
    
    def get_user_permissions(self, username: str) -> Dict:
        """Get user permissions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT r.permissions
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            return {}
            
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {str(e)}")
            return {}
    
    def create_user(self, username: str, password: str, role_name: str) -> bool:
        """Create new user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get role ID
            cursor.execute("SELECT id FROM roles WHERE name = ?", (role_name,))
            role_data = cursor.fetchone()
            
            if not role_data:
                conn.close()
                return False
            
            role_id = role_data[0]
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, role_id, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, password_hash, role_id, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create user: {str(e)}")
            return False
    
    def get_all_users(self) -> List[Dict]:
        """Get all users with their roles"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT u.id, u.username, r.name as role_name, u.created_at, u.last_login, u.is_active
                FROM users u
                JOIN roles r ON u.role_id = r.id
                ORDER BY u.created_at
            ''')
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "role_name": row[2],
                    "created_at": row[3],
                    "last_login": row[4],
                    "is_active": bool(row[5])
                })
            
            conn.close()
            return users
            
        except Exception as e:
            self.logger.error(f"Failed to get users: {str(e)}")
            return []
    
    def get_audit_logs(self, limit: int = 100, username: str = None) -> list:
        """Get audit logs with optional filtering"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = """
                SELECT id, username, action, resource, timestamp, ip_address, user_agent, success
                FROM audit_logs
                WHERE 1=1
            """
            params = []
            
            if username:
                query += " AND username = ?"
                params.append(username)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            
            logs = []
            for row in cursor.fetchall():
                logs.append({
                    "id": row[0],
                    "username": row[1],
                    "action": row[2],
                    "resource": row[3],
                    "timestamp": row[4],
                    "ip_address": row[5],
                    "user_agent": row[6],
                    "success": bool(row[7])
                })
            
            conn.close()
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to get audit logs: {str(e)}")
            return []


# Dependency functions for FastAPI
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user"""
    token = credentials.credentials
    auth_manager = AuthManager("./backup_system.db")  # This should be singleton
    
    payload = auth_manager.verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return payload


def require_permission(permission: str):
    """Decorator to require specific permission"""
    def permission_checker(current_user: dict = Depends(get_current_user)):
        if not current_user.get("permissions", {}).get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    return permission_checker
