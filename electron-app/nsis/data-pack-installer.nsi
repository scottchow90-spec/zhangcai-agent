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
!ifndef ZHANGCAI_DATA_PACK_ICO
  !error "ZHANGCAI_DATA_PACK_ICO is required"
!endif
!ifndef ZHANGCAI_7ZA
  !error "ZHANGCAI_7ZA is required"
!endif
!ifndef ZHANGCAI_DATA_PAYLOAD_PART1
  !error "ZHANGCAI_DATA_PAYLOAD_PART1 is required"
!endif
!ifndef ZHANGCAI_DATA_PAYLOAD_PART2
  !error "ZHANGCAI_DATA_PAYLOAD_PART2 is required"
!endif
!ifndef ZHANGCAI_DATA_PAYLOAD_PART3
  !error "ZHANGCAI_DATA_PAYLOAD_PART3 is required"
!endif
!ifndef ZHANGCAI_DATA_PAYLOAD_PART4
  !error "ZHANGCAI_DATA_PAYLOAD_PART4 is required"
!endif

!define ZHANGCAI_CLIENT_REG_KEY "Software\Zhangcai\Agent4319"
Name "掌财桌面端日线数据包"
OutFile "${ZHANGCAI_OUTPUT}"
InstallDir "$PROGRAMFILES64\掌财桌面端"
Icon "${ZHANGCAI_DATA_PACK_ICO}"

Var ZHANGCAI_DATA_DIALOG
Var ZHANGCAI_CLIENT_PATH_CONTROL
Var ZHANGCAI_CLIENT_BROWSE_CONTROL
Var ZHANGCAI_CLIENT_PATH
Var ZHANGCAI_RESOURCE_LIBRARY

; Accept installations whose executable was renamed by an older packaging
; build.  The client root is identified by the Electron resources marker plus
; an executable in the selected directory, not by one hard-coded filename.
Function ZhangcaiIsClientRoot
  StrCpy $0 0
  IfFileExists "$ZHANGCAI_CLIENT_PATH\*.exe" ZhangcaiDataClientHasExecutable ZhangcaiDataClientRootDone
  ZhangcaiDataClientHasExecutable:
    IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\app.asar" ZhangcaiDataClientRootValid ZhangcaiDataClientCheckAppDirectory
  ZhangcaiDataClientCheckAppDirectory:
    IfFileExists "$ZHANGCAI_CLIENT_PATH\resources\app\package.json" ZhangcaiDataClientRootValid ZhangcaiDataClientRootDone
  ZhangcaiDataClientRootValid:
    StrCpy $0 1
  ZhangcaiDataClientRootDone:
FunctionEnd

Function ZhangcaiTryDefaultClientPath
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\掌财桌面端"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\zhangcai-agent"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES\掌财桌面端"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES\zhangcai-agent"
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataDefaultClientPathDone
  StrCpy $ZHANGCAI_CLIENT_PATH "$PROGRAMFILES64\掌财桌面端"
  ZhangcaiDataDefaultClientPathDone:
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
  StrCmp $0 1 ZhangcaiDataClientPathLoaded
  StrCpy $ZHANGCAI_CLIENT_PATH ""
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    ReadRegStr $ZHANGCAI_CLIENT_PATH HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.zhangcai.agent" "InstallLocation"
  ${EndIf}
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataClientPathLoaded
  StrCpy $ZHANGCAI_CLIENT_PATH ""
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    ReadRegStr $ZHANGCAI_CLIENT_PATH HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\com.zhangcai.agent" "InstallLocation"
  ${EndIf}
  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataClientPathLoaded
  Call ZhangcaiTryDefaultClientPath
  ZhangcaiDataClientPathLoaded:
  ${If} $ZHANGCAI_CLIENT_PATH == ""
    Call ZhangcaiTryDefaultClientPath
  ${EndIf}
  ; Data follows the client directory selected on this page. This keeps the
  ; persistent data tree on D: when the client was installed on D:, while the
  ; NSIS temporary extraction area remains transient and is cleaned by NSIS.
  StrCpy $ZHANGCAI_RESOURCE_LIBRARY "$ZHANGCAI_CLIENT_PATH\data\resource-library"
FunctionEnd

Function ZhangcaiDataPageCreate
  nsDialogs::Create 1018
  Pop $ZHANGCAI_DATA_DIALOG
  ${If} $ZHANGCAI_DATA_DIALOG == error
    Abort
  ${EndIf}

  ${NSD_CreateLabel} 0 0 100% 30u "请选择已安装的掌财桌面端目录。此安装器只补充数据，不安装新的客户端。"
  Pop $0
  ${NSD_CreateLabel} 0 34u 100% 42u "选择的目录用于校验客户端身份；数据会写入该客户端目录下的 data\resource-library。请先退出掌财桌面端。"
  Pop $0
  ${NSD_CreateLabel} 0 83u 100% 30u "数据载荷约 2.35 GB，安装器约 357 MiB；i5/4 GB 预计 3–15 分钟。NSIS 将显示文件、百分比进度和当前阶段。"
  Pop $0
  ${NSD_CreateLabel} 0 117u 100% 30u "客户端目录必须包含桌面端 EXE 和 resources\app.asar（或 resources\app\package.json）。本数据包不安装或卸载 Node/Python/Harness，只写入行情数据与索引；程序代码、运行时和资源库根目录 manifest.json 不会被覆盖。"
  Pop $0
  ${NSD_CreateDirRequest} 0 154u 78% 13u "$ZHANGCAI_CLIENT_PATH"
  Pop $ZHANGCAI_CLIENT_PATH_CONTROL
  ${NSD_CreateButton} 80% 154u 20% 13u "浏览..."
  Pop $ZHANGCAI_CLIENT_BROWSE_CONTROL
  ${NSD_OnClick} $ZHANGCAI_CLIENT_BROWSE_CONTROL ZhangcaiDataBrowse

  nsDialogs::Show
FunctionEnd

Function ZhangcaiDataBrowse
  nsDialogs::SelectFolderDialog "选择掌财桌面端安装目录" "$ZHANGCAI_CLIENT_PATH"
  Pop $0
  ${If} $0 != error
    StrCpy $ZHANGCAI_CLIENT_PATH $0
    ${NSD_SetText} $ZHANGCAI_CLIENT_PATH_CONTROL $ZHANGCAI_CLIENT_PATH
  ${EndIf}
FunctionEnd

Function ZhangcaiDataPageLeave
  ${If} $ZHANGCAI_CLIENT_PATH_CONTROL != ""
    ${NSD_GetText} $ZHANGCAI_CLIENT_PATH_CONTROL $ZHANGCAI_CLIENT_PATH
  ${EndIf}
  Call ZhangcaiValidateClient
FunctionEnd

Function ZhangcaiValidateClient

  ${If} $ZHANGCAI_CLIENT_PATH == ""
    MessageBox MB_ICONSTOP|MB_OK "未指定掌财桌面端安装目录。数据包安装已取消。"
    Abort
  ${EndIf}

  Call ZhangcaiIsClientRoot
  StrCmp $0 1 ZhangcaiDataClientValid ZhangcaiDataClientInvalid

  ZhangcaiDataClientInvalid:
    MessageBox MB_ICONSTOP|MB_OK "所选目录不是有效的掌财桌面端安装目录。目录下必须同时包含桌面端 EXE，以及 resources\app.asar 或 resources\app\package.json。当前路径：$ZHANGCAI_CLIENT_PATH"
    Abort

  ZhangcaiDataClientValid:
  IfFileExists "$ZHANGCAI_CLIENT_PATH\data\resource-library\market\daily\aggregate\tdx-bars.jsonl" 0 +3
  MessageBox MB_ICONSTOP|MB_OK "该客户端已存在日线归档，已保留原数据。本数据安装包用于首次初始化；已有数据请在客户端中统一落盘或补齐，避免旧数据包覆盖较新的行情。"
  Abort
FunctionEnd

Page custom ZhangcaiDataPageCreate ZhangcaiDataPageLeave
Page instfiles

Section "日线、索引和完整性数据" SEC_DATA
  Call ZhangcaiValidateClient
  StrCpy $ZHANGCAI_RESOURCE_LIBRARY "$ZHANGCAI_CLIENT_PATH\data\resource-library"
  DetailPrint "Data package: target resource library is $ZHANGCAI_RESOURCE_LIBRARY"
  DetailPrint "Data package: preparing the embedded 7za extractor and payload parts"
  InitPluginsDir
  SetOverwrite on
  File /oname=$PLUGINSDIR\7za.exe "${ZHANGCAI_7ZA}"
  File /oname=$PLUGINSDIR\zhangcai-data.part1 "${ZHANGCAI_DATA_PAYLOAD_PART1}"
  File /oname=$PLUGINSDIR\zhangcai-data.part2 "${ZHANGCAI_DATA_PAYLOAD_PART2}"
  File /oname=$PLUGINSDIR\zhangcai-data.part3 "${ZHANGCAI_DATA_PAYLOAD_PART3}"
  File /oname=$PLUGINSDIR\zhangcai-data.part4 "${ZHANGCAI_DATA_PAYLOAD_PART4}"

  DetailPrint "Data package: merging payload parts 1/4, 2/4, 3/4 and 4/4"
  nsExec::ExecToLog 'cmd.exe /d /c copy /b "$PLUGINSDIR\zhangcai-data.part1"+"$PLUGINSDIR\zhangcai-data.part2"+"$PLUGINSDIR\zhangcai-data.part3"+"$PLUGINSDIR\zhangcai-data.part4" "$PLUGINSDIR\zhangcai-data.7z"'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "数据载荷重组失败，错误码：$0。请重新下载数据安装器后重试。"
    Abort
  ${EndIf}
  DetailPrint "Data package: writing to $ZHANGCAI_RESOURCE_LIBRARY; 7-Zip will list each file"
  nsExec::ExecToLog '"$PLUGINSDIR\7za.exe" x "$PLUGINSDIR\zhangcai-data.7z" "-o$ZHANGCAI_RESOURCE_LIBRARY" -aoa -y -bb1 -bsp1'
  Pop $0
  ${If} $0 != 0
    MessageBox MB_ICONSTOP|MB_OK "日线数据解压失败，错误码：$0。原有资源库文件未被主动删除，请检查磁盘空间后重试。"
    Abort
  ${EndIf}
  DetailPrint "Data package complete: daily bars, indexes, status, public fallback, formula evidence and integrity receipts were written"
  WriteRegStr HKCU "${ZHANGCAI_CLIENT_REG_KEY}" "DataPackClientRoot" "$ZHANGCAI_CLIENT_PATH"
  WriteRegStr HKCU "${ZHANGCAI_CLIENT_REG_KEY}" "DataPackResourceLibrary" "$ZHANGCAI_RESOURCE_LIBRARY"
SectionEnd
