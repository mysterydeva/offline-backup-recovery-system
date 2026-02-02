const { app, BrowserWindow, ipcMain, dialog, shell, Menu } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');
const log = require('electron-log');

// Configure logging
log.transports.file.level = 'info';
log.transports.console.level = 'debug';

// Global variables
let mainWindow = null;
let backendProcess = null;
const BACKEND_PORT = 8001;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;

// Application configuration
const config = {
  backendExe: path.join(process.resourcesPath, 'backend', 'BackupBackend.exe'),
  logFile: path.join(app.getPath('userData'), 'backup-system.log'),
  maxRetries: 30,
  retryDelay: 2000
};

// Initialize logging
log.info('Starting Enterprise Backup System Desktop Application');
log.info('Application path:', app.getAppPath());
log.info('User data path:', app.getPath('userData'));

// Create main application window
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    show: false,
    icon: path.join(__dirname, 'assets', 'icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      enableRemoteModule: false,
      preload: path.join(__dirname, 'preload.js'),
      webSecurity: true,
      additionalArguments: [`--backend-url=${BACKEND_URL}`]
    },
    title: 'Enterprise Backup System',
    titleBarStyle: 'default'
  });

  // Load the backend URL
  mainWindow.loadURL(BACKEND_URL);

  // Handle window state
  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
    log.info('Main window shown successfully');
  });

  // Handle window closed
  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  // Handle navigation errors
  mainWindow.webContents.on('did-fail-load', (event, errorCode, errorDescription) => {
    log.error('Failed to load backend:', errorCode, errorDescription);
    showErrorPage(errorCode, errorDescription);
  });

  // Handle external links
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Create application menu
  createApplicationMenu();

  return mainWindow;
}

// Create application menu
function createApplicationMenu() {
  const template = [
    {
      label: 'File',
      submenu: [
        {
          label: 'New Backup',
          accelerator: 'CmdOrCtrl+N',
          click: () => {
            if (mainWindow) {
              mainWindow.webContents.send('menu-new-backup');
            }
          }
        },
        { type: 'separator' },
        {
          label: 'Exit',
          accelerator: process.platform === 'darwin' ? 'Cmd+Q' : 'Ctrl+Q',
          click: () => {
            app.quit();
          }
        }
      ]
    },
    {
      label: 'View',
      submenu: [
        { label: 'Reload', accelerator: 'CmdOrCtrl+R', role: 'reload' },
        { label: 'Force Reload', accelerator: 'CmdOrCtrl+Shift+R', role: 'forceReload' },
        { type: 'separator' },
        { label: 'Actual Size', accelerator: 'CmdOrCtrl+0', role: 'resetZoom' },
        { label: 'Zoom In', accelerator: 'CmdOrCtrl+Plus', role: 'zoomIn' },
        { label: 'Zoom Out', accelerator: 'CmdOrCtrl+-', role: 'zoomOut' },
        { type: 'separator' },
        { label: 'Toggle Fullscreen', accelerator: 'F11', role: 'togglefullscreen' },
        { type: 'separator' },
        { label: 'Developer Tools', accelerator: 'F12', role: 'toggleDevTools' }
      ]
    },
    {
      label: 'Window',
      submenu: [
        { label: 'Minimize', accelerator: 'CmdOrCtrl+M', role: 'minimize' },
        { label: 'Close', accelerator: 'CmdOrCtrl+W', role: 'close' }
      ]
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'About Enterprise Backup System',
          click: () => {
            dialog.showMessageBox(mainWindow, {
              type: 'info',
              title: 'About',
              message: 'Enterprise Backup System',
              detail: 'Version 1.0.0\n\nProfessional offline backup and recovery solution for enterprise environments.\n\n© 2024 Enterprise Software Solutions'
            });
          }
        }
      ]
    }
  ];

  const menu = Menu.buildFromTemplate(template);
  Menu.setApplicationMenu(menu);
}

// Start backend server
function startBackend() {
  return new Promise((resolve, reject) => {
    log.info('Starting backend server...');
    log.info('Backend Path:', config.backendExe);
    log.info('Resources Path:', process.resourcesPath);
    log.info('App Path:', app.getAppPath());

    // Check if backend executable exists
    if (!fs.existsSync(config.backendExe)) {
      const error = `Backend executable not found: ${config.backendExe}`;
      log.error(error);
      log.error('Directory contents:', fs.readdirSync(path.dirname(config.backendExe)));
      reject(new Error(error));
      return;
    }

    log.info('Backend executable found, starting process...');

    // Start backend process
    backendProcess = spawn(config.backendExe, [], {
      stdio: ['pipe', 'pipe', 'pipe'],
      detached: false,
      windowsHide: true
    });

    // Handle backend output
    backendProcess.stdout.on('data', (data) => {
      const output = data.toString().trim();
      log.info('Backend:', output);
    });

    backendProcess.stderr.on('data', (data) => {
      const output = data.toString().trim();
      log.error('Backend Error:', output);
    });

    backendProcess.on('error', (error) => {
      log.error('Backend process error:', error);
      reject(error);
    });

    backendProcess.on('close', (code) => {
      log.info(`Backend process exited with code ${code}`);
      if (code !== 0 && !app.isQuitting) {
        log.error('Backend crashed unexpectedly');
      }
    });

    // Wait for backend to be ready
    waitForBackend(resolve, reject);
  });
}

// Wait for backend to be ready
function waitForBackend(resolve, reject) {
  let retries = 0;

  const checkBackend = async () => {
    try {
      const fetch = require('node-fetch');
      const response = await fetch(`${BACKEND_URL}/health`, { 
        timeout: 5000,
        headers: { 'User-Agent': 'Enterprise-Backup-Desktop/1.0.0' }
      });

      if (response.ok) {
        log.info('Backend is ready');
        resolve();
      } else {
        throw new Error(`Backend returned status: ${response.status}`);
      }
    } catch (error) {
      retries++;
      if (retries >= config.maxRetries) {
        reject(new Error(`Backend failed to start after ${config.maxRetries} attempts: ${error.message}`));
      } else {
        log.info(`Waiting for backend... (${retries}/${config.maxRetries})`);
        setTimeout(checkBackend, config.retryDelay);
      }
    }
  };

  // Start checking after a short delay
  setTimeout(checkBackend, 3000);
}

// Show error page
function showErrorPage(errorCode, errorDescription) {
  if (!mainWindow) return;

  const errorHtml = `
    <!DOCTYPE html>
    <html>
    <head>
      <title>Backend Error - Enterprise Backup System</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          margin: 0;
          padding: 40px;
          background: #f5f5f5;
          color: #333;
        }
        .container {
          max-width: 600px;
          margin: 0 auto;
          background: white;
          padding: 40px;
          border-radius: 8px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
          color: #e74c3c;
          margin-top: 0;
        }
        .error-code {
          background: #f8f9fa;
          padding: 10px;
          border-radius: 4px;
          font-family: monospace;
          margin: 20px 0;
        }
        .retry-btn {
          background: #3498db;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
          margin-right: 10px;
        }
        .retry-btn:hover {
          background: #2980b9;
        }
        .quit-btn {
          background: #95a5a6;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 4px;
          cursor: pointer;
          font-size: 16px;
        }
        .quit-btn:hover {
          background: #7f8c8d;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>Backend Connection Error</h1>
        <p>The Enterprise Backup System backend could not be reached. This may be due to:</p>
        <ul>
          <li>Backend service failed to start</li>
          <li>Port ${BACKEND_PORT} is already in use</li>
          <li>System resource limitations</li>
        </ul>
        
        <div class="error-code">
          Error ${errorCode}: ${errorDescription}
        </div>
        
        <div style="margin-top: 30px;">
          <button class="retry-btn" onclick="location.reload()">Retry Connection</button>
          <button class="quit-btn" onclick="window.close()">Quit Application</button>
        </div>
        
        <p style="margin-top: 30px; font-size: 14px; color: #666;">
          If this problem persists, please restart the application or contact support.
        </p>
      </div>
    </body>
    </html>
  `;

  mainWindow.loadURL(`data:text/html;charset=utf-8,${encodeURIComponent(errorHtml)}`);
}

// IPC handlers
ipcMain.handle('app-version', () => {
  return app.getVersion();
});

ipcMain.handle('app-name', () => {
  return app.getName();
});

ipcMain.handle('restart-backend', async () => {
  try {
    if (backendProcess) {
      backendProcess.kill();
      backendProcess = null;
    }
    await startBackend();
    return { success: true };
  } catch (error) {
    log.error('Failed to restart backend:', error);
    return { success: false, error: error.message };
  }
});

// App event handlers
app.whenReady().then(async () => {
  try {
    // Start backend first
    await startBackend();
    
    // Create main window
    createMainWindow();
    
    log.info('Application started successfully');
  } catch (error) {
    log.error('Failed to start application:', error);
    
    // Show error dialog
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start Enterprise Backup System:\n\n${error.message}\n\nPlease check the logs for more details.`
    );
    
    app.quit();
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createMainWindow();
  }
});

app.on('before-quit', () => {
  app.isQuitting = true;
  
  // Clean up backend process
  if (backendProcess) {
    log.info('Shutting down backend process...');
    backendProcess.kill('SIGTERM');
    
    // Force kill after 5 seconds
    setTimeout(() => {
      if (backendProcess && !backendProcess.killed) {
        backendProcess.kill('SIGKILL');
      }
    }, 5000);
  }
});

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
  log.error('Uncaught Exception:', error);
  app.quit();
});

process.on('unhandledRejection', (reason, promise) => {
  log.error('Unhandled Rejection at:', promise, 'reason:', reason);
});
