const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods that allow the renderer process to use
// the ipcRenderer without exposing the entire object
contextBridge.exposeInMainWorld('electronAPI', {
  // Application info
  getAppVersion: () => ipcRenderer.invoke('app-version'),
  getAppName: () => ipcRenderer.invoke('app-name'),
  
  // Backend control
  restartBackend: () => ipcRenderer.invoke('restart-backend'),
  
  // System info
  getPlatform: () => process.platform,
  
  // Logging
  log: (level, message) => {
    console.log(`[${level.toUpperCase()}] ${message}`);
  },
  
  // Events from main process
  onMenuAction: (callback) => {
    ipcRenderer.on('menu-new-backup', callback);
  },
  
  // Remove event listeners
  removeAllListeners: (channel) => {
    ipcRenderer.removeAllListeners(channel);
  }
});

// Inject custom styles and scripts into the web app
window.addEventListener('DOMContentLoaded', () => {
  // Add desktop app indicator
  const style = document.createElement('style');
  style.textContent = `
    .desktop-app-indicator {
      position: fixed;
      top: 10px;
      right: 10px;
      background: rgba(52, 152, 219, 0.9);
      color: white;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      z-index: 9999;
      pointer-events: none;
    }
    
    /* Hide browser-specific elements */
    .browser-only {
      display: none !important;
    }
    
    /* Adjust layout for desktop app */
    body {
      overflow-x: hidden;
    }
    
    /* Custom scrollbar for desktop app */
    ::-webkit-scrollbar {
      width: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: #f1f1f1;
    }
    
    ::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }
  `;
  document.head.appendChild(style);
  
  // Add desktop app indicator
  const indicator = document.createElement('div');
  indicator.className = 'desktop-app-indicator';
  indicator.textContent = 'Desktop App v1.0.0';
  document.body.appendChild(indicator);
  
  // Hide indicator after 5 seconds
  setTimeout(() => {
    if (indicator.parentNode) {
      indicator.parentNode.removeChild(indicator);
    }
  }, 5000);
});

// Handle keyboard shortcuts for desktop app
document.addEventListener('keydown', (event) => {
  // Ctrl/Cmd + N for new backup
  if ((event.ctrlKey || event.metaKey) && event.key === 'n') {
    event.preventDefault();
    // Trigger new backup action if available
    const newBackupBtn = document.querySelector('[data-action="new-backup"], .btn-new-backup, #new-backup');
    if (newBackupBtn) {
      newBackupBtn.click();
    }
  }
  
  // Ctrl/Cmd + R for refresh (prevent default browser refresh)
  if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
    event.preventDefault();
    window.location.reload();
  }
  
  // F11 for fullscreen
  if (event.key === 'F11') {
    event.preventDefault();
    // Toggle fullscreen via Electron API
    if (window.electronAPI) {
      window.electronAPI.toggleFullscreen();
    }
  }
});

// Enhance error handling for desktop app
window.addEventListener('error', (event) => {
  if (window.electronAPI) {
    window.electronAPI.log('error', `JavaScript Error: ${event.message} at ${event.filename}:${event.lineno}`);
  }
});

window.addEventListener('unhandledrejection', (event) => {
  if (window.electronAPI) {
    window.electronAPI.log('error', `Unhandled Promise Rejection: ${event.reason}`);
  }
});

// Add desktop-specific features
window.addEventListener('load', () => {
  // Add desktop app class to body
  document.body.classList.add('desktop-app');
  
  // Modify external links to open in system browser
  document.querySelectorAll('a[href^="http"]').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      if (window.electronAPI) {
        window.electronAPI.openExternal(link.href);
      }
    });
  });
  
  // Add desktop app notification support
  if ('Notification' in window && Notification.permission === 'default') {
    Notification.requestPermission();
  }
});

// Expose desktop app utilities
window.DesktopApp = {
  // Show notification
  showNotification: (title, body, options = {}) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      return new Notification(title, {
        body,
        icon: '/static/images/icon.png',
        ...options
      });
    }
  },
  
  // Get app info
  getAppInfo: async () => {
    if (window.electronAPI) {
      return {
        version: await window.electronAPI.getAppVersion(),
        name: await window.electronAPI.getAppName(),
        platform: window.electronAPI.getPlatform()
      };
    }
    return {};
  },
  
  // Restart backend
  restartBackend: async () => {
    if (window.electronAPI) {
      return await window.electronAPI.restartBackend();
    }
    return { success: false, error: 'Electron API not available' };
  },
  
  // Log message
  log: (level, message) => {
    if (window.electronAPI) {
      window.electronAPI.log(level, message);
    }
    console.log(`[${level.toUpperCase()}] ${message}`);
  }
};

console.log('Desktop app preload script loaded successfully');
