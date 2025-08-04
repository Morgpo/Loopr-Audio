; Inno Setup Script for Loopr Audio
; This script creates an installer for the Loopr Audio application

#define MyAppName "Loopr Audio"
#define MyAppVersion "1.0"
#define MyAppPublisher "Morgpo"
#define MyAppURL "https://github.com/Morgpo/Loopr-Audio"
#define MyAppExeName "LooprAudio.exe"
#define MyAppDescription "Simple. Elegant. Reliable audio looping for Windows."

[Setup]
; NOTE: The value of AppId uniquely identifies this application. Do not use the same AppId value in installers for other applications.
AppId={{8B5CF6A1-4F46-E5D3-1E1B-4B31262173A3}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
; Remove the following line to run in administrative install mode (install for all users)
PrivilegesRequired=lowest
OutputDir=output
OutputBaseFilename=LooprAudio_Setup
SetupIconFile=_internal\loopr_icon.ico
Compression=lzma
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
VersionInfoVersion={#MyAppVersion}
VersionInfoDescription={#MyAppDescription}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startupicon"; Description: "Start with Windows"; GroupDescription: "Startup Options"; Flags: unchecked

[Files]
; Main executable
Source: "dist\LooprAudio\LooprAudio.exe"; DestDir: "{app}"; Flags: ignoreversion

; All dependencies in _internal folder
Source: "dist\LooprAudio\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

; Documentation files
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Add to Windows startup if user selects the option
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "LooprAudio"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: startupicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Remove from startup registry when uninstalling
Filename: "reg"; Parameters: "delete ""HKCU\Software\Microsoft\Windows\CurrentVersion\Run"" /v ""LooprAudio"" /f"; Flags: runhidden

[Code]
// Custom page for installation options
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Any post-installation tasks can be added here
  end;
end;

// Clean uninstall - remove registry entries
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    // Clean up any remaining registry entries or user data if needed
    // The startup registry entry is already handled by [UninstallRun]
  end;
end;
