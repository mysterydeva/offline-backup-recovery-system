# Enterprise Backup System - Development Guide

## Project Structure

```
backup_system/
├── app/                              # Main application code
│   ├── main_fixed.py                 # FastAPI application entry point
│   ├── backup_engine.py              # Backup functionality
│   ├── restore_engine.py             # Restore functionality
│   ├── auth.py                       # Authentication system
│   ├── database.py                   # Database operations
│   ├── models.py                     # Pydantic models
│   ├── scheduler.py                  # Backup scheduling
│   ├── reports.py                    # Report generation
│   ├── retention.py                  # Retention policies
│   ├── templates/                    # Web interface templates
│   ├── config_phase3.json           # Configuration file
│   ├── requirements.txt              # Python dependencies
│   └── ...                          # Other modules
│
├── release/                          # Release packaging
│   └── windows-installer/           # Windows installer files
│       ├── run_app.py               # Application launcher
│       ├── build_exe.bat            # Windows build script
│       ├── build_exe.sh             # Linux build helper
│       ├── installer.iss            # Inno Setup script
│       ├── README_INSTALLER.md      # Installation guide
│       └── package/                 # Build output directory
│
├── README.md                        # Main project documentation
├── README_DEVELOPMENT.md            # This file
├── requirements.txt                 # Root requirements (symlink)
└── .gitignore                       # Git ignore rules
```

## Development Setup

### Prerequisites
- Python 3.8+
- pip package manager

### Quick Start

1. **Clone and navigate to project**:
   ```bash
   cd backup_system
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r app/requirements.txt
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main_fixed:app --reload --port 8001
   ```

5. **Access the dashboard**:
   Open http://127.0.0.1:8001 in your browser

### Default Credentials
- **Username**: admin
- **Password**: admin123

## Development Commands

### Running the Application
```bash
# Development mode with auto-reload
uvicorn app.main_fixed:app --reload --port 8001

# Production mode
uvicorn app.main_fixed:app --host 0.0.0.0 --port 8001

# Using the launcher script (simulates client experience)
python release/windows-installer/run_app.py
```

### Testing
```bash
# Run basic tests
python -m pytest app/tests/

# Test import functionality
python -c "import sys; sys.path.insert(0, 'app'); from main_fixed import app; print('✅ App loads successfully')"
```

### Database Operations
```bash
# Initialize database (runs automatically on first start)
python -c "import sys; sys.path.insert(0, 'app'); from database import Database; print('Database initialized')"

# Reset database (development only)
rm app/backup_system.db
```

## Building for Release

### Windows EXE Build
```bash
cd release/windows-installer
build_exe.bat
```

### Create Installer
```bash
# Requires Inno Setup to be installed
iscc installer.iss
```

## Configuration

### Main Configuration File
Location: `app/config_phase3.json`

Key settings:
- `server.port`: Application port (default: 8001)
- `server.host`: Bind address (default: 127.0.0.1)
- `database.path`: SQLite database file
- `storage.backup_path`: Backup storage directory
- `logging.level`: Log level (INFO, DEBUG, ERROR)

### Environment Variables
- `BACKUP_CONFIG_PATH`: Override config file location
- `BACKUP_LOG_LEVEL`: Override log level
- `BACKUP_PORT`: Override server port

## Architecture Overview

### Core Components
1. **FastAPI Application** (`main_fixed.py`): Web server and API endpoints
2. **Backup Engine** (`backup_engine.py`): Core backup functionality
3. **Restore Engine** (`restore_engine.py`): File restoration
4. **Authentication** (`auth.py`): User management and security
5. **Database** (`database.py`): SQLite operations and models
6. **Scheduler** (`scheduler.py`): Automated backup scheduling
7. **Reports** (`reports.py`): Backup reports and analytics
8. **Retention** (`retention.py`): Backup retention policies

### API Endpoints
- `GET /`: Dashboard interface
- `POST /auth/login`: User authentication
- `POST /backup/create`: Create backup job
- `GET /backup/list`: List backup jobs
- `POST /restore/execute`: Restore files
- `GET /system/status`: System status

### Security Features
- JWT-based authentication
- Role-based access control
- AES-256 encryption for backups
- Local-only access by default
- Secure password hashing

## Contributing Guidelines

### Code Style
- Follow PEP 8 Python style guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Keep functions focused and modular

### Testing
- Write unit tests for new features
- Test backup/restore functionality thoroughly
- Verify security implications of changes
- Test with different file types and sizes

### Git Workflow
1. Create feature branch from main
2. Implement changes with tests
3. Update documentation as needed
4. Submit pull request for review

## Troubleshooting

### Common Development Issues

#### Import Errors
```bash
# Ensure app directory is in Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)/app"
# Or in Python:
import sys; sys.path.insert(0, 'app')
```

#### Database Lock Issues
```bash
# Remove database lock file
rm app/backup_system.db-journal
```

#### Port Already in Use
```bash
# Find process using port 8001
netstat -ano | findstr :8001  # Windows
lsof -i :8001                 # Linux/Mac

# Kill process if needed
taskkill /PID <PID> /F        # Windows
kill -9 <PID>                 # Linux/Mac
```

#### Permission Issues
```bash
# Ensure proper permissions for storage directories
chmod 755 app/storage
chmod 755 app/logs
chmod 755 app/restored
```

## Performance Optimization

### Database Optimization
- Use indexes for frequent queries
- Regular database maintenance
- Consider connection pooling for high load

### Backup Performance
- Implement incremental backups
- Use compression for large files
- Parallel processing for multiple files
- Progress tracking for long operations

### Memory Management
- Stream large files instead of loading into memory
- Implement cleanup for temporary files
- Monitor memory usage during operations

## Security Best Practices

### Development Security
- Never commit secrets or API keys
- Use environment variables for sensitive config
- Implement proper input validation
- Regular security audits

### Production Security
- Change default passwords
- Use HTTPS in production
- Implement rate limiting
- Regular security updates

## Deployment Considerations

### Production Deployment
- Use proper WSGI server (Gunicorn, uWSGI)
- Implement reverse proxy (Nginx, Apache)
- Set up monitoring and logging
- Regular backup of application data

### Scaling
- Database scaling considerations
- Load balancing for multiple instances
- Distributed storage options
- Caching strategies

## Support and Resources

### Documentation
- Main README: `README.md`
- Installation Guide: `release/windows-installer/README_INSTALLER.md`
- API Documentation: Available in-app at `/docs`

### Getting Help
- Check application logs: `app/logs/backup.log`
- Review configuration: `app/config_phase3.json`
- Test with minimal setup
- Contact development team for support

---

**Last Updated**: January 2026  
**Version**: 1.0.0  
**Framework**: FastAPI + SQLite
