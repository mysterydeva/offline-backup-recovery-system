import os
import json
import psutil
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
import uvicorn
from app.database import Database
from app.backup_engine import BackupEngine
from app.restore_engine import RestoreEngine
from app.scheduler import BackupScheduler
from app.auth import AuthManager, get_current_user, require_permission
from app.models import (
    BackupResponse, RestoreResponse, BackupCreate, UserCreate, UserLogin, 
    TokenResponse, SystemStatus, RetentionStatus
)
from app.reports import ReportGenerator
from app.retention import RetentionManager
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


@app.post("/backup", response_model=BackupResponse)
async def trigger_backup():
    """Manually trigger a backup"""
    try:
        filename, size = backup_engine.create_backup()
        
        backup_create = BackupCreate(
            filename=filename,
            size=size,
            status="completed"
        )
        
        backup_id = database.create_backup_record(backup_create)
        
        return BackupResponse(
            success=True,
            message=f"Backup created successfully with ID: {backup_id}",
            backup_id=backup_id
        )
    except Exception as e:
        return BackupResponse(
            success=False,
            message=f"Backup failed: {str(e)}"
        )


@app.post("/restore/{backup_id}", response_model=RestoreResponse)
async def restore_backup(backup_id: int):
    """Restore a backup by ID"""
    try:
        backup = database.get_backup_by_id(backup_id)
        if not backup:
            raise HTTPException(status_code=404, detail="Backup not found")
        
        success = restore_engine.restore_backup(backup.filename)
        
        if success:
            return RestoreResponse(
                success=True,
                message=f"Backup {backup_id} restored successfully to {config['backup']['restore_directory']}"
            )
        else:
            return RestoreResponse(
                success=False,
                message="Restore operation failed"
            )
    except HTTPException:
        raise
    except Exception as e:
        return RestoreResponse(
            success=False,
            message=f"Restore failed: {str(e)}"
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler.scheduler.running,
        "total_backups": len(database.get_all_backups())
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
