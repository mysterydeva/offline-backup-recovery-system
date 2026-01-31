import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import Database
from backup_engine import BackupEngine
from models import BackupCreate
from retention import RetentionManager


class BackupScheduler:
    def __init__(self, config: dict, database: Database, backup_engine: BackupEngine):
        self.config = config
        self.database = database
        self.backup_engine = backup_engine
        self.scheduler = BackgroundScheduler()
        self.retention_manager = RetentionManager(config, database)
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger(__name__)
    
    def scheduled_backup(self):
        """Scheduled backup job"""
        try:
            self.logger.info("Starting scheduled backup")
            filename, size, checksum, encrypted = self.backup_engine.create_backup()
            
            backup_create = BackupCreate(
                filename=filename,
                size=size,
                status="completed"
            )
            
            backup_id = self.database.create_backup_record(backup_create, checksum, encrypted)
            self.logger.info(f"Scheduled backup completed with ID: {backup_id}")
            
            # Apply retention policy if enabled
            if self.config.get("retention", {}).get("enabled", False):
                cleanup_results = self.retention_manager.apply_retention_policy()
                if cleanup_results["deleted_count"] > 0:
                    self.logger.info(f"Retention cleanup removed {cleanup_results['deleted_count']} old backups")
            
        except Exception as e:
            self.logger.error(f"Scheduled backup failed: {str(e)}")
    
    def start(self):
        """Start the scheduler"""
        if self.config["scheduler"]["enabled"]:
            interval_minutes = self.config["scheduler"]["interval_minutes"]
            self.scheduler.add_job(
                func=self.scheduled_backup,
                trigger=IntervalTrigger(minutes=interval_minutes),
                id='backup_job',
                name='Scheduled Backup',
                replace_existing=True
            )
            self.scheduler.start()
            self.logger.info(f"Scheduler started - backup every {interval_minutes} minute(s)")
        else:
            self.logger.info("Scheduler is disabled")
    
    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler stopped")
