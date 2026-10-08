Unicode true
!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!define ZHANGCAI_ENV_BASELINE_VERSION "0.1.9"

!define ZHANGCAI_TDX_DOWNLOAD_URL "https://data.tdx.com.cn/mock/new_tdx_mock.exe"
!define ZHANGCAI_TDX_REG_KEY "Software\Zhangcai\Agent4319"

; Keep the standard NSIS file list and smooth progress bar visible. The
; percentage is owned by NSIS, while the custom pages below give a truthful
; estimate before the irreversible file-copy phase starts.
ShowInstDetails show
InstProgressFlags smooth

; The integrated main installer owns both the program layer and its private
; runtime. The install-root data directory must survive uninstall and an
; in-place upgrade, but code/runtime are safe to replace as one unit.
!macro customRemoveFiles
  SetOutPath "$TEMP"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pak"
  Delete "$INSTDIR\*.bin"
  Delete "$INSTDIR\*.dat"
  Delete "$INSTDIR\LICENSE*"
  Delete "$INSTDIR\version"
  Delete "$INSTDIR\vk_swiftshader_icd.json"
  RMDir /r "$INSTDIR\locales"
  ; The main installer owns the complete private runtime and program layer.
  ; Data is deliberately outside these paths and is preserved.
  RMDir /r "$INSTDIR\resources\app"
  RMDir /r "$INSTDIR\resources\runtime"
  RMDir /r "$INSTDIR\resources\deepseek-harness"
  RMDir /r "$INSTDIR\resources\resource-library"
  Delete "$INSTDIR\resources\app.asar"
  Delete "$INSTDIR\resources\elevate.exe"
  RMDir "$INSTDIR\resources\app"
  RMDir "$INSTDIR\resources"
  RMDir "$INSTDIR"
!macroend

!ifndef BUILD_UNINSTALLER

Var ZHANGCAI_TDX_DIALOG
Var ZHANGCAI_TDX_PATH_CONTROL
Var ZHANGCAI_TDX_BROWSE_CONTROL
Var ZHANGCAI_TDX_PATH
Var ZHANGCAI_ENV_DIALOG
Var ZHANGCAI_RUNTIME_SUMMARY
Var ZHANGCAI_DATA_BACKUP

Function ZhangcaiPreserveLegacyData
  ; The old 0.1.0 uninstaller predates customRemoveFiles and deletes data.
  ; Copy it outside that uninstaller's target before calling it. Keep the
  ; backup even after success so failed upgrades remain recoverable.
  ; Once a version carrying this marker is installed, customRemoveFiles
  ; preserves $INSTDIR\\data itself, so later upgrades do not need to make a
  ; second full-size safety copy.
  ReadRegStr $R7 HKCU "${ZHANGCAI_TDX_REG_KEY}" "DataSafeUninstaller"
  ${If} $R7 == "1"
    Goto PreserveDataDone
  ${EndIf}
  ReadRegStr $R8 HKCU "${ZHANGCAI_TDX_REG_KEY}" "InstallRoot"
  ${If} $R8 == ""
    ReadRegStr $R8 HKCU "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${UNINSTALL_APP_KEY}" "InstallLocation"
  ${EndIf}
  ${If} $R8 == ""
    ReadRegStr $R8 HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${UNINSTALL_APP_KEY}" "InstallLocation"
  ${EndIf}
  ${If} $R8 != ""
  ${AndIf} $ZHANGCAI_DATA_BACKUP == ""
    IfFileExists "$R8\data\*.*" 0 PreserveDataDone
    System::Call 'kernel32::GetTickCount() i .r9'
    StrCpy $ZHANGCAI_DATA_BACKUP "$R8.data-backup-${VERSION}-$9"
    nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$R8\data" "$ZHANGCAI_DATA_BACKUP" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ'
    Pop $0
    ${If} $0 > 7
    ${OrIf} $0 == "error"
      StrCpy $ZHANGCAI_DATA_BACKUP ""
      MessageBox MB_ICONSTOP|MB_OK "无法完成旧版数据备份。原数据未删除，请退出客户端并检查磁盘空间和写入权限后重试。"
      Abort
    ${EndIf}
  ${EndIf}
  PreserveDataDone:
FunctionEnd

Function ZhangcaiDetectEmbeddedRuntime
  StrCpy $ZHANGCAI_RUNTIME_SUMMARY ""
  IfFileExists "$INSTDIR\resources\runtime\node\node.exe" ZhangcaiNodePresent ZhangcaiNodeMissing
  ZhangcaiNodePresent:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Node.js 24.19.0 detected;"
    Goto ZhangcaiNodeDone
  ZhangcaiNodeMissing:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Node.js 24.19.0 missing;"
  ZhangcaiNodeDone:
  IfFileExists "$INSTDIR\resources\runtime\python\python.exe" ZhangcaiPythonPresent ZhangcaiPythonMissing
  ZhangcaiPythonPresent:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Python 3.12.14 detected;"
    Goto ZhangcaiPythonDone
  ZhangcaiPythonMissing:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Python 3.12.14 missing;"
  ZhangcaiPythonDone:
  IfFileExists "$INSTDIR\resources\deepseek-harness\lib\bin.js" ZhangcaiHarnessPresent ZhangcaiHarnessMissing
  ZhangcaiHarnessPresent:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Harness 0.1.2-rc.1 detected;"
    Goto ZhangcaiHarnessDone
  ZhangcaiHarnessMissing:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Harness 0.1.2-rc.1 missing;"
  ZhangcaiHarnessDone:
  IfFileExists "$INSTDIR\resources\app\node_modules\vinext\dist\cli.js" 0 ZhangcaiVinextMissing
  StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Vinext 1.0.0-beta.5 detected."
  Goto ZhangcaiRuntimeVersionDone
  ZhangcaiVinextMissing:
    StrCpy $ZHANGCAI_RUNTIME_SUMMARY "$ZHANGCAI_RUNTIME_SUMMARY Vinext 1.0.0-beta.5 missing."
  ZhangcaiRuntimeVersionDone:
FunctionEnd

Function ZhangcaiValidateEnvironmentLayer
  DetailPrint "Environment check: bundled private runtime will be installed in the selected directory"
  Call ZhangcaiDetectEmbeddedRuntime
  DetailPrint "Environment baseline: ${ZHANGCAI_ENV_BASELINE_VERSION}; detected: $ZHANGCAI_RUNTIME_SUMMARY"
FunctionEnd

Function ZhangcaiEnvironmentPageCreate
  SetDetailsPrint both
  Call ZhangcaiDetectEmbeddedRuntime
  nsDialogs::Create 1018
  Pop $ZHANGCAI_ENV_DIALOG
  ${If} $ZHANGCAI_ENV_DIALOG == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 30u "正在检查 Windows 安装环境和掌财私有运行环境。本主安装包会一并写入固定版本的 Node.js、Python、Vinext 和 DeepSeek Harness。"
  Pop $0
  ${NSD_CreateLabel} 0 35u 100% 42u "白板电脑无需先安装运行环境包；本安装包会把 Electron、页面、桥接脚本、技能、公式种子以及可复用的私有运行环境写入同一个安装目录。"
  Pop $0
  ${NSD_CreateLabel} 0 83u 100% 30u "本机预计安装时间：约 20–90 秒。安装过程中会显示当前程序文件组和 NSIS 百分比进度。"
  Pop $0
  ${NSD_CreateLabel} 0 117u 100% 54u "本次版本环境检测：$ZHANGCAI_RUNTIME_SUMMARY"
  Pop $0
  ${NSD_CreateLabel} 0 175u 100% 30u "系统全局版本即使更高也不会被卸载；桌面端只调用环境包固定的私有版本，避免影响客户机上的其他程序。"
  Pop $0
  ${NSD_CreateLabel} 0 209u 100% 30u "DeepSeek API 密钥由用户首次启动后在桌面端配置，不会写入安装包。"
  Pop $0

  nsDialogs::Show
FunctionEnd

Function ZhangcaiValidateEnvironment
  DetailPrint "Environment check: $ZHANGCAI_RUNTIME_SUMMARY"
  DetailPrint "Environment policy: system-wide runtimes are untouched; only the private app copy is installed"
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
  StrCmp $0 "" ZhangcaiWindowsVersionMissing
  IntCmp $0 10240 ZhangcaiWindowsVersionOk ZhangcaiWindowsVersionFail ZhangcaiWindowsVersionOk
  ZhangcaiWindowsVersionMissing:
    MessageBox MB_ICONSTOP|MB_OK "掌财桌面端当前只支持 Windows 10/11。"
    Abort
  ZhangcaiWindowsVersionFail:
    MessageBox MB_ICONSTOP|MB_OK "掌财桌面端当前只支持 Windows 10/11。"
    Abort
  ZhangcaiWindowsVersionOk:
  IfFileExists "$WINDIR\SysWOW64\kernel32.dll" ZhangcaiArchitectureOk ZhangcaiArchitectureFail
  ZhangcaiArchitectureFail:
    MessageBox MB_ICONSTOP|MB_OK "当前安装包为 x64 版本，需要 64 位 Windows 10/11。"
    Abort
  ZhangcaiArchitectureOk:
  IfFileExists "$SYSDIR\\reg.exe" ZhangcaiEnvironmentRegOk
  MessageBox MB_ICONSTOP|MB_OK "当前 Windows 环境缺少 reg.exe，无法保存通达信目录。请修复 Windows 系统组件后再安装。"
  Abort

  ZhangcaiEnvironmentRegOk:
  IfFileExists "$SYSDIR\\WindowsPowerShell\\v1.0\\powershell.exe" ZhangcaiEnvironmentPowerShellOk
  MessageBox MB_ICONSTOP|MB_OK "当前 Windows 环境缺少 Windows PowerShell，无法完成桌面端运行环境检查。请修复系统组件后再安装。"
  Abort

  ZhangcaiEnvironmentPowerShellOk:
  ; Runtime files are embedded in this installer, so a missing or older
  ; pre-existing layer is not a reason to abort. The installer replaces only
  ; the private copy it owns; global Node/Python installations are untouched.
  Call ZhangcaiValidateEnvironmentLayer
FunctionEnd

Function ZhangcaiTdxPageCreate
  ReadRegStr $ZHANGCAI_TDX_PATH HKCU "${ZHANGCAI_TDX_REG_KEY}" "TDXRoot"
  nsDialogs::Create 1018
  Pop $ZHANGCAI_TDX_DIALOG
  ${If} $ZHANGCAI_TDX_DIALOG == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 30u "请选择通达信安装目录。主程序不会把通达信 EXE 打进安装包，也不会替用户安装通达信。"
  Pop $0
  ${NSD_CreateLabel} 0 34u 100% 24u "目录应包含 vipdoc 或 T0002 子目录；没有通达信目录时请取消安装并先下载安装。"
  Pop $0
  ${NSD_CreateLabel} 0 60u 100% 24u "确认目录后才会开始复制掌财文件；如果目录为空，安装器会打开通达信下载页面并停在当前页面。"
  Pop $0
  ${NSD_CreateDirRequest} 0 92u 78% 13u "$ZHANGCAI_TDX_PATH"
  Pop $ZHANGCAI_TDX_PATH_CONTROL
  ${NSD_CreateButton} 80% 92u 20% 13u "浏览..."
  Pop $ZHANGCAI_TDX_BROWSE_CONTROL
  ${NSD_OnClick} $ZHANGCAI_TDX_BROWSE_CONTROL ZhangcaiTdxBrowse

  nsDialogs::Show
FunctionEnd

Function ZhangcaiTdxBrowse
  nsDialogs::SelectFolderDialog "选择通达信安装目录" "$ZHANGCAI_TDX_PATH"
  Pop $0
  ${If} $0 != error
    StrCpy $ZHANGCAI_TDX_PATH $0
    ${NSD_SetText} $ZHANGCAI_TDX_PATH_CONTROL $ZHANGCAI_TDX_PATH
  ${EndIf}
FunctionEnd

Function ZhangcaiValidateTdx
  ${If} $ZHANGCAI_TDX_PATH_CONTROL != ""
    ${NSD_GetText} $ZHANGCAI_TDX_PATH_CONTROL $ZHANGCAI_TDX_PATH
  ${EndIf}

  ${If} $ZHANGCAI_TDX_PATH == ""
    ExecShell "open" "${ZHANGCAI_TDX_DOWNLOAD_URL}"
    MessageBox MB_ICONSTOP|MB_OK "未提供通达信安装目录。已打开下载页面，请先下载安装通达信后再运行本安装程序。"
    Abort
  ${EndIf}

  IfFileExists "$ZHANGCAI_TDX_PATH\vipdoc\*.*" ZhangcaiTdxValid
  IfFileExists "$ZHANGCAI_TDX_PATH\T0002\*.*" ZhangcaiTdxValid
  ExecShell "open" "${ZHANGCAI_TDX_DOWNLOAD_URL}"
  MessageBox MB_ICONSTOP|MB_OK "所选目录不是可识别的通达信安装目录。已打开下载页面，请确认目录后再安装。"
  Abort

  ZhangcaiTdxValid:
  Call ZhangcaiPreserveLegacyData
  WriteRegStr HKCU "${ZHANGCAI_TDX_REG_KEY}" "TDXRoot" "$ZHANGCAI_TDX_PATH"
FunctionEnd

!macro customPageAfterChangeDir
  Page custom ZhangcaiEnvironmentPageCreate ZhangcaiValidateEnvironment
  Page custom ZhangcaiTdxPageCreate ZhangcaiValidateTdx
!macroend

; Do not validate again from customInstall. electron-builder invokes that
; macro during the install-files phase, which made a missing TDX path appear
; as a failure around 90% after files had already been copied. The two custom
; pages above validate and persist the choices before Page instfiles.
!macro customInstall
  ${If} $ZHANGCAI_DATA_BACKUP != ""
    DetailPrint "Restoring legacy data; the original backup is kept at $ZHANGCAI_DATA_BACKUP"
    nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$ZHANGCAI_DATA_BACKUP" "$INSTDIR\data" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ'
    Pop $0
    ${If} $0 > 7
    ${OrIf} $0 == "error"
      MessageBox MB_ICONSTOP|MB_OK "旧版数据恢复未完成，备份仍保留在 $ZHANGCAI_DATA_BACKUP。请保留备份并修复磁盘空间或写入权限。"
      Abort
    ${EndIf}
  ${EndIf}
  CreateDirectory "$INSTDIR\data\resource-library\desktop"
  WriteINIStr "$INSTDIR\data\resource-library\desktop\installer.ini" "TDX" "Root" "$ZHANGCAI_TDX_PATH"
  WriteRegStr HKCU "${ZHANGCAI_TDX_REG_KEY}" "InstallRoot" "$INSTDIR"
  WriteRegStr HKCU "${ZHANGCAI_TDX_REG_KEY}" "DataSafeUninstaller" "1"
  DetailPrint "File group: Zhangcai Desktop page code and web assets"
  DetailPrint "File group: private Node.js 24.19.0, Python 3.12.14 and Vinext production dependencies"
  DetailPrint "File group: DeepSeek Harness 0.1.2-rc.1 and pinned runtime dependencies"
  DetailPrint "File group: Electron desktop shell and application entrypoint"
  DetailPrint "File group: home page, chat page, bridge scripts and skills"
  DetailPrint "File group: resource-library/evidence/formulas/package (TQ formula seed)"
  DetailPrint "File group: desktop runtime state and TongdaXin directory configuration"
  DetailPrint "Zhangcai Desktop: writing files to $INSTDIR"
  DetailPrint "Zhangcai Desktop: bundled runtime installed; writable data root is $INSTDIR\data"
!macroend

!macro customInit
  IfSilent 0 +3
  SetErrorLevel 2
  Quit
!macroend

!endif
