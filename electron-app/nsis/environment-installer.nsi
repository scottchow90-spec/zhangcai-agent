Unicode true
RequestExecutionLevel user
ManifestSupportedOS win7
XPStyle on
ShowInstDetails show
InstProgressFlags smooth
BrandingText "Zhangcai Desktop"
SetCompress off

!include "nsDialogs.nsh"
!include "LogicLib.nsh"

!ifndef ZHANGCAI_OUTPUT
  !error "ZHANGCAI_OUTPUT is required"
!endif
!ifndef ZHANGCAI_INSTALLER_ICO
  !error "ZHANGCAI_INSTALLER_ICO is required"
!endif
!ifndef ZHANGCAI_7ZA
  !error "ZHANGCAI_7ZA is required"
!endif
!ifndef ZHANGCAI_ENV_PAYLOAD_PART1
  !error "ZHANGCAI_ENV_PAYLOAD_PART1 is required"
!endif
!ifndef ZHANGCAI_ENV_PAYLOAD_PART2
  !error "ZHANGCAI_ENV_PAYLOAD_PART2 is required"
!endif
!ifndef ZHANGCAI_ENV_PAYLOAD_PART3
  !error "ZHANGCAI_ENV_PAYLOAD_PART3 is required"
!endif
!ifndef ZHANGCAI_ENV_PAYLOAD_PART4
  !error "ZHANGCAI_ENV_PAYLOAD_PART4 is required"
!endif
!ifndef ZHANGCAI_ENV_BASELINE_VERSION
  !error "ZHANGCAI_ENV_BASELINE_VERSION is required"
!endif

!define ZHANGCAI_REG_KEY "Software\Zhangcai\Agent4319"
Name "掌财桌面端运行环境"
OutFile "${ZHANGCAI_OUTPUT}"
InstallDir "$PROGRAMFILES64\掌财桌面端"
Icon "${ZHANGCAI_INSTALLER_ICO}"

Var ZHANGCAI_ENV_DIALOG
Var ZHANGCAI_ENV_PATH_CONTROL
Var ZHANGCAI_ENV_BROWSE_CONTROL
Var ZHANGCAI_ENV_ROOT
Var ZHANGCAI_ENV_SUMMARY
Var ZHANGCAI_ENV_REUSE

Function .onInit
  IfSilent 0 +3
  SetErrorLevel 2
  Quit
  SetRegView 64
  SetDetailsPrint both
  ReadRegStr $ZHANGCAI_ENV_ROOT HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentRoot"
  ${If} $ZHANGCAI_ENV_ROOT == ""
    ReadRegStr $ZHANGCAI_ENV_ROOT HKCU "${ZHANGCAI_REG_KEY}" "InstallRoot"
  ${EndIf}
  ${If} $ZHANGCAI_ENV_ROOT == ""
    StrCpy $ZHANGCAI_ENV_ROOT "$PROGRAMFILES64\掌财桌面端"
  ${EndIf}
FunctionEnd

Function ZhangcaiDetectEnvironment
  StrCpy $ZHANGCAI_ENV_REUSE "0"
  StrCpy $ZHANGCAI_ENV_SUMMARY "No reusable private runtime found; the pinned dependencies will be installed."
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\runtime\node\node.exe" 0 ZhangcaiEnvironmentMissing
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\runtime\python\python.exe" 0 ZhangcaiEnvironmentMissing
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\deepseek-harness\lib\bin.js" 0 ZhangcaiEnvironmentMissing
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\app\node_modules\vinext\dist\cli.js" 0 ZhangcaiEnvironmentMissing
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" 0 ZhangcaiEnvironmentMissing
  ReadINIStr $0 "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" "Environment" "BaselineVersion"
  StrCmp $0 "${ZHANGCAI_ENV_BASELINE_VERSION}" 0 ZhangcaiEnvironmentVersionMismatch
  ReadINIStr $1 "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" "Environment" "HarnessVersion"
  ReadINIStr $2 "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" "Environment" "NodeVersion"
  ReadINIStr $3 "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" "Environment" "PythonVersion"
  StrCpy $ZHANGCAI_ENV_REUSE "1"
  StrCpy $ZHANGCAI_ENV_SUMMARY "Matching runtime found: Node.js $2, Python $3, DeepSeek Harness $1 and Vinext; runtime files will be reused."
  Goto ZhangcaiEnvironmentDetectionDone

  ZhangcaiEnvironmentVersionMismatch:
    StrCpy $ZHANGCAI_ENV_SUMMARY "An old or mismatched runtime was found (baseline $0); only the app private runtime will be replaced."
    Goto ZhangcaiEnvironmentDetectionDone

  ZhangcaiEnvironmentMissing:
    StrCpy $ZHANGCAI_ENV_SUMMARY "The complete runtime is missing; Node.js 24.19.0, Python 3.12.14, DeepSeek Harness 0.1.2-rc.1 and Vinext will be installed."

  ZhangcaiEnvironmentDetectionDone:
FunctionEnd

Function ZhangcaiEnvironmentPageCreate
  Call ZhangcaiDetectEnvironment
  nsDialogs::Create 1018
  Pop $ZHANGCAI_ENV_DIALOG
  ${If} $ZHANGCAI_ENV_DIALOG == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 28u "这是独立的掌财桌面端运行环境包，不包含主程序、首页、聊天页面或用户数据。"
  Pop $0
  ${NSD_CreateLabel} 0 34u 100% 42u "环境包只安装主程序需要的私有 Node.js、Python、DeepSeek Harness、Vinext 生产依赖和版本清单；不会安装或卸载系统全局 Node.js、Python、pnpm，也不会修改其他软件。"
  Pop $0
  ${NSD_CreateLabel} 0 82u 100% 42u "检测结果：$ZHANGCAI_ENV_SUMMARY"
  Pop $0
  ${NSD_CreateLabel} 0 130u 100% 30u "请选择与随后主程序相同的安装目录。环境包完成后，再运行掌财桌面端主程序安装包。"
  Pop $0
  ${NSD_CreateDirRequest} 0 168u 78% 13u "$ZHANGCAI_ENV_ROOT"
  Pop $ZHANGCAI_ENV_PATH_CONTROL
  ${NSD_CreateButton} 80% 168u 20% 13u "浏览..."
  Pop $ZHANGCAI_ENV_BROWSE_CONTROL
  ${NSD_OnClick} $ZHANGCAI_ENV_BROWSE_CONTROL ZhangcaiEnvironmentBrowse
  ${NSD_CreateLabel} 0 204u 100% 28u "预计时间：首次安装约 2–8 分钟；如果已检测到完全匹配环境，将跳过复制。安装页会显示当前文件组和百分比。"
  Pop $0

  nsDialogs::Show
FunctionEnd

Function ZhangcaiEnvironmentBrowse
  nsDialogs::SelectFolderDialog "选择掌财运行环境目录" "$ZHANGCAI_ENV_ROOT"
  Pop $0
  ${If} $0 != error
    StrCpy $ZHANGCAI_ENV_ROOT $0
    ${NSD_SetText} $ZHANGCAI_ENV_PATH_CONTROL $ZHANGCAI_ENV_ROOT
    Call ZhangcaiDetectEnvironment
  ${EndIf}
FunctionEnd

Function ZhangcaiValidateWindows
  ReadRegStr $0 HKLM "SOFTWARE\Microsoft\Windows NT\CurrentVersion" "CurrentBuildNumber"
  StrCmp $0 "" ZhangcaiWindowsInvalid
  IntCmp $0 10240 ZhangcaiWindowsValid ZhangcaiWindowsInvalid ZhangcaiWindowsValid
  ZhangcaiWindowsInvalid:
    MessageBox MB_ICONSTOP|MB_OK "掌财桌面端运行环境包只支持 64 位 Windows 10/11。"
    Abort
  ZhangcaiWindowsValid:
  IfFileExists "$WINDIR\SysWOW64\kernel32.dll" 0 ZhangcaiWindowsArchitectureInvalid
  IfFileExists "$SYSDIR\reg.exe" 0 ZhangcaiWindowsComponentInvalid
  IfFileExists "$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" 0 ZhangcaiWindowsComponentInvalid
  Goto ZhangcaiWindowsDone
  ZhangcaiWindowsArchitectureInvalid:
    MessageBox MB_ICONSTOP|MB_OK "当前环境包是 x64 版本，需要 64 位 Windows。"
    Abort
  ZhangcaiWindowsComponentInvalid:
    MessageBox MB_ICONSTOP|MB_OK "Windows 缺少 reg.exe 或 Windows PowerShell，无法完成环境配置。请先修复系统组件。"
    Abort
  ZhangcaiWindowsDone:
FunctionEnd

Function ZhangcaiValidateEnvironmentTarget
  ${NSD_GetText} $ZHANGCAI_ENV_PATH_CONTROL $ZHANGCAI_ENV_ROOT
  ${If} $ZHANGCAI_ENV_ROOT == ""
    MessageBox MB_ICONSTOP|MB_OK "未指定掌财运行环境目录，安装已取消。"
    Abort
  ${EndIf}
  Call ZhangcaiValidateWindows
FunctionEnd

Page custom ZhangcaiEnvironmentPageCreate ZhangcaiValidateEnvironmentTarget
Page instfiles

Section "掌财桌面端运行环境" SEC_ENVIRONMENT
  Call ZhangcaiValidateEnvironmentTarget
  Call ZhangcaiDetectEnvironment
  DetailPrint "Environment check: $ZHANGCAI_ENV_SUMMARY"
  ${If} $ZHANGCAI_ENV_REUSE == "1"
    DetailPrint "Environment install: matching versions reused; no runtime files copied"
    WriteRegStr HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentRoot" "$ZHANGCAI_ENV_ROOT"
    WriteRegStr HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentBaselineVersion" "${ZHANGCAI_ENV_BASELINE_VERSION}"
    Goto ZhangcaiEnvironmentInstallDone
  ${EndIf}

  InitPluginsDir
  SetOverwrite on
  File /oname=$PLUGINSDIR\7za.exe "${ZHANGCAI_7ZA}"
  File /oname=$PLUGINSDIR\zhangcai-environment.part1 "${ZHANGCAI_ENV_PAYLOAD_PART1}"
  File /oname=$PLUGINSDIR\zhangcai-environment.part2 "${ZHANGCAI_ENV_PAYLOAD_PART2}"
  File /oname=$PLUGINSDIR\zhangcai-environment.part3 "${ZHANGCAI_ENV_PAYLOAD_PART3}"
  File /oname=$PLUGINSDIR\zhangcai-environment.part4 "${ZHANGCAI_ENV_PAYLOAD_PART4}"

  DetailPrint "Environment install: merging payload parts 1/4, 2/4, 3/4 and 4/4"
  nsExec::ExecToLog 'cmd.exe /d /c copy /b "$PLUGINSDIR\zhangcai-environment.part1"+"$PLUGINSDIR\zhangcai-environment.part2"+"$PLUGINSDIR\zhangcai-environment.part3"+"$PLUGINSDIR\zhangcai-environment.part4" "$PLUGINSDIR\zhangcai-environment.7z"'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "环境载荷重组失败，错误码：$0。请重新下载环境包后重试。"
    Abort
  ${EndIf}

  DetailPrint "Environment install: extracting Node.js, Python, Harness and production page dependencies"
  nsExec::ExecToLog '"$PLUGINSDIR\7za.exe" x "$PLUGINSDIR\zhangcai-environment.7z" "-o$PLUGINSDIR\environment" -aoa -y -bb1 -bsp1'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "环境载荷展开失败，错误码：$0。主程序尚未安装。"
    Abort
  ${EndIf}

  DetailPrint "Environment install: writing resources\runtime"
  nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$PLUGINSDIR\environment\resources\runtime" "$ZHANGCAI_ENV_ROOT\resources\runtime" /MIR /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP'
  Pop $0
  ${If} $0 > 7
  ${OrIf} $0 == "error"
    MessageBox MB_ICONSTOP|MB_OK "resources\runtime 写入失败，错误码：$0。请检查磁盘空间和权限。"
    Abort
  ${EndIf}

  DetailPrint "Environment install: writing resources\deepseek-harness"
  nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$PLUGINSDIR\environment\resources\deepseek-harness" "$ZHANGCAI_ENV_ROOT\resources\deepseek-harness" /MIR /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP'
  Pop $0
  ${If} $0 > 7
  ${OrIf} $0 == "error"
    MessageBox MB_ICONSTOP|MB_OK "resources\deepseek-harness 写入失败，错误码：$0。请检查磁盘空间和权限。"
    Abort
  ${EndIf}

  DetailPrint "Environment install: writing resources\app\node_modules"
  nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$PLUGINSDIR\environment\resources\app\node_modules" "$ZHANGCAI_ENV_ROOT\resources\app\node_modules" /MIR /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP'
  Pop $0
  ${If} $0 > 7
  ${OrIf} $0 == "error"
    MessageBox MB_ICONSTOP|MB_OK "resources\app\node_modules 写入失败，错误码：$0。请检查磁盘空间和权限。"
    Abort
  ${EndIf}

  WriteRegStr HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentRoot" "$ZHANGCAI_ENV_ROOT"
  WriteRegStr HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentBaselineVersion" "${ZHANGCAI_ENV_BASELINE_VERSION}"
  DetailPrint "Environment install: baseline ${ZHANGCAI_ENV_BASELINE_VERSION} completed; the main app can now be installed"

  ZhangcaiEnvironmentInstallDone:
  DetailPrint "Environment install complete: the main app and user data were not changed"
SectionEnd
