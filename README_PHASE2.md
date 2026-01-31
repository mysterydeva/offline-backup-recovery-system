# 🏢 Phase-2 Enterprise Backup System

Advanced offline backup and recovery system with enterprise-grade security and management features.

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Enterprise System
```bash
uvicorn main_enterprise:app --reload --port 8001
```

### 3. Access Dashboard
Open your browser and navigate to: **http://localhost:8001**

**Default Login:**
- Username: `admin`
- Password: `admin123`

## ✅ Phase-2 Enterprise Features

### 🔐 **1. AES-256 Encryption Module**
- **File**: `security/encryption.py`
- **Features**:
  - Automatic AES-256 encryption for all backup files
  - Secure key generation and storage
  - Fernet-based encryption implementation
  - Encrypted files stored as `.zip.enc`

### 🛡️ **2. SHA-256 Integrity Verification**
- **File**: `security/integrity.py`
- **Features**:
  - SHA-256 checksum generation for all backups
  - Pre-restore integrity verification
  - Database storage of checksums
  - Automatic corruption detection

### 📊 **3. Retention Policy Manager**
- **File**: `retention.py`
- **Features**:
  - Configurable backup retention rules
  - Age-based cleanup (delete backups older than X days)
  - Count-based cleanup (keep last N backups)
  - Automatic cleanup after each backup

### 💾 **4. Storage Quota & Disk Monitoring**
- **Features**:
  - Real-time storage usage tracking
  - Configurable storage quotas
  - Disk space monitoring
  - Quota warning system
  - Backup blocking when quota exceeded

### 👥 **5. User Authentication & RBAC**
- **File**: `auth.py`
- **Features**:
  - Local user authentication system
  - Role-based access control (RBAC)
  - Three roles: Admin, Operator, Viewer
  - JWT token-based authentication
  - Password hashing with bcrypt
  - Comprehensive audit logging

**Role Permissions:**
- **Admin**: backup + restore + manage users + export
- **Operator**: backup + restore + view
- **Viewer**: view only

### 📈 **6. Report Generator (CSV + PDF)**
- **File**: `reports.py`
- **Features**:
  - CSV export of backup history
  - PDF report generation with ReportLab
  - Audit log export
  - Professional report formatting

### 🔍 **7. Alert & Audit Log System**
- **Features**:
  - Comprehensive audit logging
  - User action tracking
  - Success/failure logging
  - IP address and user agent tracking
  - Real-time dashboard alerts

### 🎨 **8. Enterprise Dashboard UI**
- **File**: `templates/dashboard_enterprise.html`
- **Features**:
  - Modern responsive design
  - Real-time system statistics
  - Role-based button visibility
  - Storage quota indicators
  - Interactive backup management
  - Professional UI/UX

## 📁 Updated Project Structure

```
backup_system/
├── main_enterprise.py         # Enterprise FastAPI application
├── config.json               # Enhanced configuration
├── database.py               # Updated with new schema
├── backup_engine.py          # With encryption & integrity
├── restore_engine.py         # With decryption & verification
├── scheduler.py              # With retention policy
├── models.py                 # Extended data models
├── auth.py                   # Authentication & RBAC
├── retention.py              # Retention policy manager
├── reports.py                # Report generator
├── security/                 # Security modules
│   ├── encryption.py         # AES-256 encryption
│   └── integrity.py          # SHA-256 verification
├── templates/                # Enterprise UI templates
│   ├── dashboard_enterprise.html
│   └── login.html
├── config/                   # Configuration directory
│   └── secret.key           # Encryption key (auto-generated)
├── storage/backups/          # Encrypted backup storage
├── restored/                 # Restore target
├── logs/                     # Enhanced logging
└── requirements.txt          # Updated dependencies
```

## 🔧 Configuration

Enhanced `config.json` with Phase-2 settings:

```json
{
    "backup": {
        "encryption_enabled": true
    },
    "retention": {
        "max_backups": 10,
        "max_age_days": 30,
        "enabled": true
    },
    "quota": {
        "max_storage_mb": 500,
        "warning_threshold_mb": 400
    },
    "security": {
        "encryption_key_file": "./config/secret.key",
        "session_timeout_hours": 24
    }
}
```

## 📡 Enterprise API Endpoints

### Authentication
- `POST /api/login` - User authentication
- `POST /api/logout` - User logout

### Dashboard & Management
- `GET /api/dashboard` - Dashboard data with system status
- `POST /api/backup` - Create encrypted backup
- `POST /api/restore/{id}` - Restore with verification

### Reports & Export
- `GET /api/export/csv` - Export backup history as CSV
- `GET /api/export/pdf` - Generate PDF report

### User Management (Admin Only)
- `GET /api/users` - List all users
- `POST /api/users` - Create new user

### System
- `GET /api/health` - Enhanced health check

## 🗄️ Database Schema Updates

### Enhanced Backups Table
```sql
CREATE TABLE backups (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL,
    size INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    checksum TEXT,              -- NEW: SHA-256 checksum
    encrypted INTEGER DEFAULT 0  -- NEW: Encryption flag
);
```

### New Tables
```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    last_login TEXT,
    is_active INTEGER DEFAULT 1
);

-- Roles table
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    permissions TEXT NOT NULL
);

-- Audit logs table
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    resource TEXT,
    timestamp TEXT NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    success INTEGER DEFAULT 1
);
```

## 🔒 Security Features

- **AES-256 Encryption**: All backup files encrypted with military-grade encryption
- **SHA-256 Integrity**: Cryptographic checksums for data integrity verification
- **Secure Key Storage**: Encryption keys stored securely in local files
- **Password Hashing**: bcrypt-based password hashing
- **JWT Authentication**: Secure token-based authentication
- **Audit Logging**: Comprehensive security audit trail
- **Role-Based Access**: Granular permission control

## 📊 System Monitoring

Real-time dashboard shows:
- Total backups count
- Storage usage (MB)
- Free disk space (GB)
- Last backup timestamp
- Scheduler status
- Retention policy status
- Quota warnings

## 🛠️ Requirements

- Python 3.8+
- **New Dependencies**:
  - `cryptography` - AES-256 encryption
  - `bcrypt` - Password hashing
  - `PyJWT` - JWT authentication
  - `reportlab` - PDF generation
  - `psutil` - System monitoring

## 🚀 Deployment

The system maintains full offline capability:
- No external API dependencies
- Local authentication only
- On-premise encryption key storage
- Self-contained audit logging

## 📈 Performance & Scalability

- **Efficient Encryption**: Stream-based encryption for large files
- **Database Optimization**: Indexed queries for fast backup retrieval
- **Retention Automation**: Automatic cleanup prevents storage bloat
- **Concurrent Operations**: Async operations for better performance

## 🔍 Testing & Validation

All Phase-2 features tested:
- ✅ AES-256 encryption/decryption
- ✅ SHA-256 integrity verification
- ✅ Database schema updates
- ✅ User authentication & RBAC
- ✅ Retention policy enforcement
- ✅ Report generation
- ✅ Dashboard functionality
- ✅ API endpoint security

## 📝 Migration from Phase-1

1. **Backup existing data**: Export current backup data
2. **Update dependencies**: Install new requirements
3. **Run migration**: Database schema updates automatically
4. **Configure settings**: Update config.json with new options
5. **Test authentication**: Create user accounts
6. **Verify encryption**: Test backup/restore workflow

The Phase-2 system is backward compatible and will automatically migrate existing data.
