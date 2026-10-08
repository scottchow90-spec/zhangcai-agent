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
!ifndef ZHANGCAI_PROGRAM_PAYLOAD_PART1
  !error "ZHANGCAI_PROGRAM_PAYLOAD_PART1 is required"
!endif
!ifndef ZHANGCAI_PROGRAM_PAYLOAD_PART2
  !error "ZHANGCAI_PROGRAM_PAYLOAD_PART2 is required"
!endif
!ifndef ZHANGCAI_PROGRAM_PAYLOAD_PART3
  !error "ZHANGCAI_PROGRAM_PAYLOAD_PART3 is required"
!endif
!ifndef ZHANGCAI_PROGRAM_PAYLOAD_PART4
  !error "ZHANGCAI_PROGRAM_PAYLOAD_PART4 is required"
!endif

!define ZHANGCAI_CLIENT_REG_KEY "Software\Zhangcai\Agent4319"
Name "掌财桌面端程序更新"
OutFile "${ZHANGCAI_OUTPUT}"
InstallDir "$PROGRAMFILES64\掌财桌面端"
Icon "${ZHANGCAI_INSTALLER_ICO}"

Var ZHANGCAI_UPDATE_DIALOG
Var ZHANGCAI_CLIENT_PATH_CONTROL
Var ZHANGCAI_CLIENT_BROWSE_CONTROL
Var ZHANGCAI_CLIENT_PATH

; The executable name was fixed in early builds, but an existing installation
; may have been created with a different product/executable name.  The
; resources marker is the identity needed for an in-place program update.
Function ZhangcaiIsClientRoot
  StrCpy $0 0
  IfFileExists "$ZHANGCAI_CLIENT_PATH\*.exe" ZhangcaiClientHasExecutable ZhangcaiClientRootDone
  ZhangcaiClientHasExecutable:
    IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\app.asar" ZhangcaiClientRootValid ZhangcaiClientCheckAppDirectory
  ZhangcaiClientCheckAppDirectory:
    IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\app\package.json" ZhangcaiClientRootValid ZhangcaiClientRootDone
  ZhangcaiClientRootValid:
    StrCpy $0 1
  ZhangcaiClientRootDone:
FunctionEnd

Function ZhangcaiTryDefaultClientPath
  ; Keep both the product-name path and package-name path compatible.  A valid
  ; registry path on another drive is preferred by .onInit before this list.
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\掌财桌面端"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\zhangcai-agent"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES\掌财桌面端"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES\zhangcai-agent"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\掌财桌面端"
  ZhangcaiDefaultClientPathDone:
FunctionEnd

Function .onInit
  IfSilent 0 +3
  SetErrorLevel 2
  Quit
  SetRegView 64
  SetDetailsPrint both
  StrCpy $ZHANGCAI_CLIENT_PATH ""
  ReadRegStr $ZHANGCAI_CLIENT_PATH HKCU "${ZHANGCAI_CLIENT_REG_KEY}" "InstallRoot"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiClientPathLoaded
  StrCpy $ZHANGCAI_CLIENT_PATH ""
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    ReadRegStr $ZHANGCAI_CLIENT_PATH HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.zhangcai.agent" "InstallLocation"
  ${EndIf}
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiClientPathLoaded
  StrCpy $ZHANGCAI_CLIENT_PATH ""
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    ReadRegStr $ZHANGCAI_CLIENT_PATH HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.zhangcai.agent" "InstallLocation"
  ${EndIf}
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiClientPathLoaded
  Call ZhangcaiTryDefaultClientPath
  ZhangcaiClientPathLoaded:
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    Call ZhangcaiTryDefaultClientPath
  ${EndIf}
FunctionEnd

Function ZhangcaiUpdatePageCreate
  nsDialogs::Create 1018
  Pop $ZHANGCAI_UPDATE_DIALOG
  ${If} $ZHANGCAI_UPDATE_DIALOG == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 16u "这是掌财桌面端程序更新包，只更新页面、桥接、技能和公式种子。"
  Pop $0
  ${NSD_CreateLabel} 0 20u 100% 28u "Node.js、Python、DeepSeek Harness、Electron 和运行依赖属于环境层；本包不重装、不卸载、不覆盖。"
  Pop $0
  ${NSD_CreateLabel} 0 52u 100% 24u "请先退出掌财桌面端。更新显示文件组、文件进度和百分比；data\resource-library 会保留。"
  Pop $0
  ${NSD_CreateLabel} 0 82u 100% 12u "掌财桌面端安装目录："
  Pop $0
  ${NSD_CreateDirRequest} 0 96u 76% 14u "$ZHANGCAI_CLIENT_PATH"
  Pop $ZHANGCAI_CLIENT_PATH_CONTROL
  ${NSD_CreateButton} 78% 96u 22% 14u "浏览..."
  Pop $ZHANGCAI_CLIENT_BROWSE_CONTROL
  ${NSD_OnClick} $ZHANGCAI_CLIENT_BROWSE_CONTROL ZhangcaiUpdateBrowse

  nsDialogs::Show
FunctionEnd

Function ZhangcaiUpdateBrowse
  nsDialogs::SelectFolderDialog "选择掌财桌面端安装目录" "$ZHANGCAI_CLIENT_PATH"
  Pop $0
  ${If} $0 != error
    StrCpy $ZHANGCAI_CLIENT_PATH $0
    ${NSD_SetText} $ZHANGCAI_CLIENT_PATH_CONTROL $ZHANGCAI_CLIENT_PATH
  ${EndIf}
FunctionEnd

Function ZhangcaiValidateClient
  ${If} $ZHANGCAI_CLIENT_PATH_CONTROL != ""
    ${NSD_GetText} $ZHANGCAI_CLIENT_PATH_CONTROL $ZHANGCAI_CLIENT_PATH
  ${EndIf}

  ${If} $ZHANGCAI_CLIENT_PATH == ""
    MessageBox MB_ICONSTOP|MB_OK "未指定掌财桌面端安装目录，程序更新已取消。"
    Abort
  ${EndIf}
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiClientRootAccepted ZhangcaiClientInvalid

  ZhangcaiClientRootAccepted:
  IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\runtime\node\node.exe" 0 ZhangcaiEnvironmentInvalid
  IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\runtime\python\python.exe" 0 ZhangcaiEnvironmentInvalid
  IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\deepseek-harness\lib\bin.js" 0 ZhangcaiEnvironmentInvalid
  IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\app\node_modules\vinext\dist\cli.js" 0 ZhangcaiEnvironmentInvalid
  IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\runtime\environment-version.ini" 0 ZhangcaiEnvironmentInvalid
  Goto ZhangcaiClientValid

  ZhangcaiEnvironmentInvalid:
    MessageBox MB_ICONSTOP|MB_OK "所选目录缺少掌财基线运行环境（Node.js、Python、Harness 或 Vinext）。请先安装完整主程序，再运行程序更新包。"
    Abort

  ZhangcaiClientInvalid:
    MessageBox MB_ICONSTOP|MB_OK "所选目录不是有效的掌财桌面端安装目录。目录下必须同时包含桌面端 EXE，以及 resources\app.asar 或 resources\app\package.json。当前路径：$ZHANGCAI_CLIENT_PATH"
    Abort

  ZhangcaiClientValid:
FunctionEnd

Page custom ZhangcaiUpdatePageCreate ZhangcaiValidateClient
Page instfiles

Section "掌财桌面端程序文件" SEC_PROGRAM
  Call ZhangcaiValidateClient
  DetailPrint "Program update: target install directory is $ZHANGCAI_CLIENT_PATH"
  DetailPrint "Program update: existing Node.js, Python, Harness and Vinext runtime will be reused"
  DetailPrint "Program update: data\resource-library, market data and reports will not be overwritten"
  InitPluginsDir
  SetOverwrite on
  File /oname=$PLUGINSDIR\7za.exe "${ZHANGCAI_7ZA}"
  File /oname=$PLUGINSDIR\zhangcai-program.part1 "${ZHANGCAI_PROGRAM_PAYLOAD_PART1}"
  File /oname=$PLUGINSDIR\zhangcai-program.part2 "${ZHANGCAI_PROGRAM_PAYLOAD_PART2}"
  File /oname=$PLUGINSDIR\zhangcai-program.part3 "${ZHANGCAI_PROGRAM_PAYLOAD_PART3}"
  File /oname=$PLUGINSDIR\zhangcai-program.part4 "${ZHANGCAI_PROGRAM_PAYLOAD_PART4}"

  DetailPrint "Program update: merging payload parts 1/4, 2/4, 3/4 and 4/4"
  nsExec::ExecToLog 'cmd.exe /d /c copy /b "$PLUGINSDIR\zhangcai-program.part1"+"$PLUGINSDIR\zhangcai-program.part2"+"$PLUGINSDIR\zhangcai-program.part3"+"$PLUGINSDIR\zhangcai-program.part4" "$PLUGINSDIR\zhangcai-program.7z"'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "程序载荷重组失败，错误码：$0。请重新下载更新包后重试。"
    Abort
  ${EndIf}

  DetailPrint "Program update: extracting page and bridge files to a temporary directory"
  nsExec::ExecToLog '"$PLUGINSDIR\7za.exe" x "$PLUGINSDIR\zhangcai-program.7z" "-o$PLUGINSDIR\program" -aoa -y -bb1 -bsp1'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "程序载荷展开失败，错误码：$0。现有安装未主动删除。"
    Abort
  ${EndIf}

  ; Remove only the previous program layer. The environment node_modules,
  ; runtime, Harness, Electron files and user data are deliberately untouched.
  DetailPrint "Program update: removing old page and bridge files; runtime and user data are preserved"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\dist"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\scripts"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\harness-skills"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\lib"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\public"
  RMDir /r "$ZHANGCAI_CLIENT_PATH\resources\app\config"
  Delete "$ZHANGCAI_CLIENT_PATH\resources\app\agent-server.mjs"
  Delete "$ZHANGCAI_CLIENT_PATH\resources\app\dependency-manifest.json"
  Delete "$ZHANGCAI_CLIENT_PATH\resources\app\harness-headless.patch.yml"
  Delete "$ZHANGCAI_CLIENT_PATH\resources\app\package.json"
  Delete "$ZHANGCAI_CLIENT_PATH\resources\app.asar"

  DetailPrint "Program update: writing resources\app.asar"
  CopyFiles /SILENT "$PLUGINSDIR\program\resources\app.asar" "$ZHANGCAI_CLIENT_PATH\resources"
  DetailPrint "Program update: writing resources\app (pages, skills, scripts and bridge)"
  nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$PLUGINSDIR\program\resources\app" "$ZHANGCAI_CLIENT_PATH\resources\app" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP'
  Pop $0
  ${If} $0 > 7
  ${OrIf} $0 == "error"
    MessageBox MB_ICONSTOP|MB_OK "页面和桥接文件写入失败，错误码：$0。请保留当前目录并重新运行环境包或更新包。"
    Abort
  ${EndIf}

  DetailPrint "Program update: writing the embedded formula seed; data\resource-library is untouched"
  nsExec::ExecToLog '"$SYSDIR\robocopy.exe" "$PLUGINSDIR\program\resources\resource-library" "$ZHANGCAI_CLIENT_PATH\resources\resource-library" /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP'
  Pop $0
  ${If} $0 > 7
  ${OrIf} $0 == "error"
    MessageBox MB_ICONSTOP|MB_OK "内置公式种子写入失败，错误码：$0。现有数据目录未被删除。"
    Abort
  ${EndIf}
  WriteRegStr HKCU "${ZHANGCAI_CLIENT_REG_KEY}" "InstallRoot" "$ZHANGCAI_CLIENT_PATH"
  DetailPrint "Program update complete: the runtime layer and data\resource-library were preserved"
SectionEnd
