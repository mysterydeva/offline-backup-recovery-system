[Setup]
; Enterprise Backup System - Inno Setup Installer Script
; Professional Windows Installer Configuration

; Basic installer information
AppName=Enterprise Backup System
AppVersion=1.0.0
AppPublisher=Enterprise Software Solutions
AppPublisherURL=https://enterprise-backup.com
AppSupportURL=https://enterprise-backup.com/support
AppUpdatesURL=https://enterprise-backup.com/updates

; Default installation directory
DefaultDirName={pf}\Enterprise Backup System
DefaultGroupName=Enterprise Backup System

; Output installer filename
OutputBaseFilename=BackupSystem_Setup
OutputDir=.

; Installer compression and optimization
Compression=lzma2/max
SolidCompression=yes
InternalCompressLevel=max

; Modern UI settings
SetupIconFile=package\BackupSystem.exe
WizardImageFile=package\templates\static\images\logo.png
WizardSmallImageFile=package\templates\static\images\logo-small.png

; Windows version compatibility
MinVersion=6.1sp1
PrivilegesRequired=admin

; License and information
LicenseFile=..\..\..\LICENSE.txt
InfoBeforeFile=README_INSTALLER.md

; Architectures
ArchitecturesAllowed=x64 x86
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; OnlyBelowVersion: 6.1; Flags: unchecked

[Files]
; Main executable and application files
Source: "package\BackupSystem.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "package\config_phase3.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "package\config.json"; DestDir: "{app}"; Flags: ignoreversion; Tasks: 
Source: "package\requirements.txt"; DestDir: "{app}"; Flags: ignoreversion

; Templates directory (web interface)
Source: "package\templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs createallsubdirs

; Storage and data directories
Source: "package\storage\*"; DestDir: "{app}\storage"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "package\logs\*"; DestDir: "{app}\logs"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "package\restored\*"; DestDir: "{app}\restored"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "package\sandbox_restore\*"; DestDir: "{app}\sandbox_restore"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "package\config\*"; DestDir: "{app}\config"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation
Source: "README_INSTALLER.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\..\..\README.md"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
; Ensure data directories exist with proper permissions
Name: "{app}\storage\backups"; Permissions: users-modify
Name: "{app}\logs"; Permissions: users-modify
Name: "{app}\restored"; Permissions: users-modify
Name: "{app}\sandbox_restore"; Permissions: users-modify

[Icons]
; Start Menu shortcuts
Name: "{group}\Enterprise Backup System"; Filename: "{app}\BackupSystem.exe"; WorkingDir: "{app}"; IconFilename: "{app}\BackupSystem.exe"; Comment: "Launch Enterprise Backup System Dashboard"
Name: "{group}\Uninstall Enterprise Backup System"; Filename: "{uninstallexe}"

; Desktop shortcut
Name: "{userdesktop}\Enterprise Backup System"; Filename: "{app}\BackupSystem.exe"; WorkingDir: "{app}"; Tasks: desktopicon; IconFilename: "{app}\BackupSystem.exe"; Comment: "Launch Enterprise Backup System Dashboard"

; Quick Launch shortcut
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\Enterprise Backup System"; Filename: "{app}\BackupSystem.exe"; WorkingDir: "{app}"; Tasks: quicklaunchicon; IconFilename: "{app}\BackupSystem.exe"; Comment: "Launch Enterprise Backup System Dashboard"

[Run]
; Launch application after installation
Filename: "{app}\BackupSystem.exe"; Description: "Launch Enterprise Backup System"; Flags: nowait postinstall skipifsilent

[Registry]
; Register application for Windows
Root: HKLM; Subkey: "SOFTWARE\Enterprise Backup System"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Enterprise Backup System"; ValueType: string; ValueName: "Version"; ValueData: "1.0.0"
Root: HKLM; Subkey: "SOFTWARE\Enterprise Backup System"; ValueType: string; ValueName: "DisplayName"; ValueData: "Enterprise Backup System"

; Add to Windows Programs and Features
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Enterprise Backup System_is1"; ValueType: string; ValueName: "DisplayName"; ValueData: "Enterprise Backup System"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Enterprise Backup System_is1"; ValueType: string; ValueName: "InstallLocation"; ValueData: "{app}"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Enterprise Backup System_is1"; ValueType: string; ValueName: "DisplayVersion"; ValueData: "1.0.0"
Root: HKLM; Subkey: "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Enterprise Backup System_is1"; ValueType: string; ValueName: "Publisher"; ValueData: "Enterprise Software Solutions"

[UninstallDelete]
; Remove user data directories (optional - uncomment if desired)
; Type: filesandordirs; Name: "{app}\storage\backups"
; Type: filesandordirs; Name: "{app}\logs"
; Type: filesandordirs; Name: "{app}\restored"
; Type: filesandordirs; Name: "{app}\sandbox_restore"

[Code]
function GetUninstallString(): String;
var
  sUnInstPath: String;
begin
  sUnInstPath := ExpandConstant('Software\Microsoft\Windows\CurrentVersion\Uninstall\Enterprise Backup System_is1_is1');
  Result := '';
  if not RegQueryStringValue(HKLM, sUnInstPath, 'UninstallString', Result) then
    RegQueryStringValue(HKCU, sUnInstPath, 'UninstallString', Result);
end;

function IsUpgrade(): Boolean;
begin
  Result := (GetUninstallString() <> '');
end;

function InitializeSetup(): Boolean;
begin
  Result := True;
  if IsUpgrade() then
  begin
    if MsgBox('Enterprise Backup System is already installed. Do you want to upgrade?', mbInformation, MB_YESNO) = IDNO then
      Result := False;
  end;
end;
