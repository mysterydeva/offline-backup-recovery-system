import csv
import io
import logging
from datetime import datetime
from typing import List
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.database import Database
from app.models import BackupRecordExtended, AuditLog


class ReportGenerator:
    def __init__(self, database: Database):
        self.database = database
        self.logger = logging.getLogger(__name__)
    
    def generate_backup_csv(self) -> str:
        """Generate CSV report of all backups"""
        try:
            backups = self.database.get_all_backups()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Filename', 'Size (bytes)', 'Created At', 
                'Status', 'Checksum', 'Encrypted'
            ])
            
            # Write data
            for backup in backups:
                writer.writerow([
                    backup.id,
                    backup.filename,
                    backup.size,
                    backup.created_at.isoformat(),
                    backup.status,
                    backup.checksum or '',
                    'Yes' if backup.encrypted else 'No'
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            self.logger.info("CSV backup report generated successfully")
            return csv_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate CSV report: {str(e)}")
            return ""
    
    def generate_backup_pdf(self) -> bytes:
        """Generate PDF report of all backups"""
        try:
            backups = self.database.get_all_backups()
            
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=18,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            # Build PDF content
            story = []
            
            # Title
            story.append(Paragraph("Backup System Report", title_style))
            story.append(Spacer(1, 12))
            
            # Report metadata
            story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"Total Backups: {len(backups)}", styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Create table data
            table_data = [['ID', 'Filename', 'Size', 'Created At', 'Status', 'Encrypted']]
            
            for backup in backups:
                table_data.append([
                    str(backup.id),
                    backup.filename[:30] + '...' if len(backup.filename) > 30 else backup.filename,
                    f"{backup.size:,} bytes",
                    backup.created_at.strftime('%Y-%m-%d %H:%M'),
                    backup.status,
                    'Yes' if backup.encrypted else 'No'
                ])
            
            # Create table
            table = Table(table_data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
            ]))
            
            story.append(table)
            
            # Build PDF
            doc.build(story)
            
            # Get PDF content
            pdf_content = buffer.getvalue()
            buffer.close()
            
            self.logger.info("PDF backup report generated successfully")
            return pdf_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate PDF report: {str(e)}")
            return b""
    
    def generate_audit_csv(self) -> str:
        """Generate CSV report of audit logs"""
        try:
            audit_logs = self._get_audit_logs()
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'ID', 'Username', 'Action', 'Resource', 'Timestamp', 
                'IP Address', 'Success'
            ])
            
            # Write data
            for log in audit_logs:
                writer.writerow([
                    log.id,
                    log.username,
                    log.action,
                    log.resource or '',
                    log.timestamp.isoformat(),
                    log.ip_address or '',
                    'Yes' if log.success else 'No'
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            self.logger.info("CSV audit report generated successfully")
            return csv_content
            
        except Exception as e:
            self.logger.error(f"Failed to generate audit CSV report: {str(e)}")
            return ""
    
    def _get_audit_logs(self) -> List[AuditLog]:
        """Get audit logs from database"""
        try:
            import sqlite3
            conn = sqlite3.connect(self.database.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, action, resource, timestamp, ip_address, user_agent, success
                FROM audit_logs
                ORDER BY timestamp DESC
                LIMIT 1000
            ''')
            
            logs = []
            for row in cursor.fetchall():
                logs.append(AuditLog(
                    id=row[0],
                    username=row[1],
                    action=row[2],
                    resource=row[3],
                    timestamp=datetime.fromisoformat(row[4]),
                    ip_address=row[5],
                    user_agent=row[6],
                    success=bool(row[7])
                ))
            
            conn.close()
            return logs
            
        except Exception as e:
            self.logger.error(f"Failed to get audit logs: {str(e)}")
            return []
