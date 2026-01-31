import os
import json
import psutil
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn
from database import Database
from backup_engine import BackupEngine
from restore_engine import RestoreEngine
from scheduler import BackupScheduler
from auth import AuthManager, get_current_user, require_permission
from models import (
    BackupResponse, RestoreResponse, BackupCreate, UserCreate, UserLogin, 
    TokenResponse, SystemStatus, RetentionStatus
)
from reports import ReportGenerator
from retention import RetentionManager
import logging

# Setup logging to avoid duplicate handlers
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('./logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Enterprise Backup System", description="Advanced offline backup and recovery system")

# Load configuration
with open('config.json', 'r') as f:
    config = json.load(f)

# Initialize components
database = Database(config["database"]["path"])
backup_engine = BackupEngine(config)
restore_engine = RestoreEngine(config)
scheduler = BackupScheduler(config, database, backup_engine)
auth_manager = AuthManager(config["database"]["path"])
retention_manager = RetentionManager(config, database)
report_generator = ReportGenerator(database)

# Setup templates
templates = Jinja2Templates(directory="templates")

# Global scheduler instance to prevent duplicates
_scheduler_started = False


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "message": None,
            "success": None,
            "user": None  # Will be set by auth
        }
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "error": None
        }
    )


@app.post("/api/login")
async def login(login_data: UserLogin):
    """Authenticate user and return token"""
    try:
        user = auth_manager.authenticate_user(login_data.username, login_data.password)
        
        if not user:
            auth_manager.log_audit(login_data.username, "login", success=False)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )
        
        # Create access token
        access_token = auth_manager.create_access_token(
            data={"sub": user["username"], "role": user["role_name"]}
        )
        
        auth_manager.log_audit(user["username"], "login", success=True)
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            user=user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@app.post("/api/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    auth_manager.log_audit(current_user["username"], "logout", success=True)
    return {"message": "Logged out successfully"}


@app.get("/api/dashboard")
async def get_dashboard_data(current_user: dict = Depends(get_current_user)):
    """Get dashboard data"""
    try:
        backups = database.get_all_backups()
        
        # Calculate system status
        total_backups = len(backups)
        last_backup_time = backups[0].created_at if backups else None
        
        # Calculate storage usage
        storage_used = 0
        for backup in backups:
            backup_file = os.path.join(config["backup"]["storage_directory"], backup.filename)
            if os.path.exists(backup_file):
                storage_used += os.path.getsize(backup_file)
        
        # Get disk space
        disk_usage = psutil.disk_usage('/')
        disk_free_gb = disk_usage.free / (1024**3)
        
        system_status = SystemStatus(
            total_backups=total_backups,
            storage_used_mb=round(storage_used / (1024**2), 2),
            disk_free_gb=round(disk_free_gb, 2),
            last_backup_time=last_backup_time,
            scheduler_running=scheduler.scheduler.running
        )
        
        # Get retention status
        retention_status = retention_manager.get_retention_status()
        
        return {
            "backups": [backup.dict() for backup in backups],
            "system_status": system_status.dict(),
            "retention_status": retention_status,
            "user": current_user
        }
        
    except Exception as e:
        logger.error(f"Dashboard data error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get dashboard data"
        )


@app.post("/api/backup")
async def trigger_backup(current_user: dict = Depends(require_permission("backup"))):
    """Manually trigger a backup"""
    try:
        # Check storage quota
        quota_mb = config.get("quota", {}).get("max_storage_mb", 500)
        current_usage = retention_manager.get_retention_status()["total_size_mb"]
        
        if current_usage >= quota_mb:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Storage quota exceeded ({current_usage:.2f}MB / {quota_mb}MB)"
            )
        
        filename, size, checksum, encrypted = backup_engine.create_backup()
        
        backup_create = BackupCreate(
            filename=filename,
            size=size,
            status="completed"
        )
        
        backup_id = database.create_backup_record(backup_create, checksum, encrypted)
        
        auth_manager.log_audit(
            current_user["username"], 
            "backup", 
            f"Created backup ID {backup_id}",
            success=True
        )
        
        return BackupResponse(
            success=True,
            message=f"Backup created successfully with ID: {backup_id}",
            backup_id=backup_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        auth_manager.log_audit(
            current_user["username"], 
            "backup", 
            "Manual backup failed",
            success=False
        )
        return BackupResponse(
            success=False,
            message=f"Backup failed: {str(e)}"
        )


@app.post("/api/restore/{backup_id}")
async def restore_backup(
    backup_id: int, 
    current_user: dict = Depends(require_permission("restore"))
):
    """Restore a backup by ID"""
    try:
        backup = database.get_backup_by_id(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        success = restore_engine.restore_backup(backup.filename, backup.checksum)
        
        if success:
            auth_manager.log_audit(
                current_user["username"], 
                "restore", 
                f"Restored backup ID {backup_id}",
                success=True
            )
            
            return RestoreResponse(
                success=True,
                message=f"Backup {backup_id} restored successfully to {config['backup']['restore_directory']}"
            )
        else:
            auth_manager.log_audit(
                current_user["username"], 
                "restore", 
                f"Failed to restore backup ID {backup_id}",
                success=False
            )
            
            return RestoreResponse(
                success=False,
                message="Restore operation failed"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        auth_manager.log_audit(
            current_user["username"], 
            "restore", 
            f"Restore error for backup ID {backup_id}",
            success=False
        )
        
        return RestoreResponse(
            success=False,
            message=f"Restore failed: {str(e)}"
        )


@app.get("/api/export/csv")
async def export_csv(current_user: dict = Depends(require_permission("export"))):
    """Export backup data as CSV"""
    try:
        csv_content = report_generator.generate_backup_csv()
        
        auth_manager.log_audit(
            current_user["username"], 
            "export", 
            "CSV export",
            success=True
        )
        
        return JSONResponse(
            content=csv_content,
            headers={
                "Content-Disposition": "attachment; filename=backups.csv",
                "Content-Type": "text/csv"
            }
        )
        
    except Exception as e:
        auth_manager.log_audit(
            current_user["username"], 
            "export", 
            "CSV export failed",
            success=False
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate CSV export"
        )


@app.get("/api/export/pdf")
async def export_pdf(current_user: dict = Depends(require_permission("export"))):
    """Export backup data as PDF"""
    try:
        pdf_content = report_generator.generate_backup_pdf()
        
        auth_manager.log_audit(
            current_user["username"], 
            "export", 
            "PDF export",
            success=True
        )
        
        return JSONResponse(
            content=pdf_content,
            headers={
                "Content-Disposition": "attachment; filename=backups.pdf",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        auth_manager.log_audit(
            current_user["username"], 
            "export", 
            "PDF export failed",
            success=False
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate PDF export"
        )


@app.get("/api/users")
async def get_users(current_user: dict = Depends(require_permission("manage_users"))):
    """Get all users (admin only)"""
    try:
        users = auth_manager.get_all_users()
        return {"users": users}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get users"
        )


@app.post("/api/users")
async def create_user(
    user_data: UserCreate,
    current_user: dict = Depends(require_permission("manage_users"))
):
    """Create new user (admin only)"""
    try:
        success = auth_manager.create_user(
            user_data.username,
            user_data.password,
            user_data.role_name
        )
        
        if success:
            auth_manager.log_audit(
                current_user["username"], 
                "create_user", 
                f"Created user {user_data.username}",
                success=True
            )
            
            return {"message": f"User {user_data.username} created successfully"}
        else:
            auth_manager.log_audit(
                current_user["username"], 
                "create_user", 
                f"Failed to create user {user_data.username}",
                success=False
            )
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.scheduler.running,
        "total_backups": len(database.get_all_backups()),
        "timestamp": datetime.now().isoformat()
    }


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global _scheduler_started
    if not _scheduler_started:
        scheduler.start()
        _scheduler_started = True
        logger.info("Scheduler started on application startup")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global _scheduler_started
    if _scheduler_started:
        scheduler.stop()
        _scheduler_started = False
        logger.info("Scheduler stopped on application shutdown")


if __name__ == "__main__":
    uvicorn.run(app, host=config["server"]["host"], port=config["server"]["port"], reload=True)
