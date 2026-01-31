from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel


class BackupRecord(BaseModel):
    id: int
    filename: str
    size: int
    created_at: datetime
    status: str


class BackupCreate(BaseModel):
    filename: str
    size: int
    status: str = "completed"


class BackupResponse(BaseModel):
    success: bool
    message: str
    backup_id: Optional[int] = None


class RestoreResponse(BaseModel):
    success: bool
    message: str


class UserCreate(BaseModel):
    username: str
    password: str
    role_name: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    role_name: str
    created_at: datetime
    last_login: Optional[str]
    is_active: bool


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: Dict


class BackupRecordExtended(BackupRecord):
    checksum: Optional[str] = None
    encrypted: bool = False
    backup_type: str = "full"
    app_name: str = "default"
    verified: bool = False
    parent_backup_id: Optional[int] = None


class ApplicationCreate(BaseModel):
    name: str
    source_path: str
    description: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    name: str
    source_path: str
    description: Optional[str]
    created_at: datetime
    is_active: bool


class BackupFileMetadata(BaseModel):
    backup_id: int
    file_path: str
    file_size: int
    file_mtime: float
    file_hash: str
    backup_type: str


class BackupRequest(BaseModel):
    backup_type: str = "full"  # full, incremental, differential
    app_name: str = "default"


class DatabaseConfig(BaseModel):
    type: str  # sqlite, mysql, postgres
    host: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    name: Optional[str] = None
    path: Optional[str] = None  # For SQLite


class AuditLog(BaseModel):
    id: int
    username: str
    action: str
    resource: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: bool


class RetentionStatus(BaseModel):
    total_backups: int
    old_backups: int
    excess_backups: int
    max_backups: int
    max_age_days: int
    total_size_bytes: int
    total_size_mb: float


class SystemStatus(BaseModel):
    total_backups: int
    storage_used_mb: float
    disk_free_gb: float
    last_backup_time: Optional[datetime]
    scheduler_running: bool
