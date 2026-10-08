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
!ifndef ZHANGCAI_ENV_BASELINE_VERSION
  !error "ZHANGCAI_ENV_BASELINE_VERSION is required"
!endif

!define ZHANGCAI_REG_KEY "Software\Zhangcai\Agent4319"
Name "掌财桌面端运行环境卸载"
OutFile "${ZHANGCAI_OUTPUT}"
InstallDir "$PROGRAMFILES64\掌财桌面端"
Icon "${ZHANGCAI_INSTALLER_ICO}"

Var ZHANGCAI_ENV_DIALOG
Var ZHANGCAI_ENV_PATH_CONTROL
Var ZHANGCAI_ENV_BROWSE_CONTROL
Var ZHANGCAI_ENV_ROOT

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

Function ZhangcaiEnvironmentUninstallPageCreate
  nsDialogs::Create 1018
  Pop $ZHANGCAI_ENV_DIALOG
  ${If} $ZHANGCAI_ENV_DIALOG == error
    Abort
  ${EndIf}
  ${NSD_CreateLabel} 0 0 100% 35u "环境卸载包只移除掌财私有运行环境，不会卸载系统全局 Node.js、Python 或 pnpm。"
  Pop $0
  ${NSD_CreateLabel} 0 42u 100% 54u "将移除：resources\\runtime、resources\\deepseek-harness、resources\\app\\node_modules。主程序文件、data\\resource-library、行情、报告、公式落盘和通达信目录配置会保留。卸载后主程序暂时不能运行，重新安装环境包即可恢复。"
  Pop $0
  ${NSD_CreateLabel} 0 104u 100% 26u "请先退出掌财桌面端，再选择与主程序相同的安装目录。"
  Pop $0
  ${NSD_CreateDirRequest} 0 140u 78% 13u "$ZHANGCAI_ENV_ROOT"
  Pop $ZHANGCAI_ENV_PATH_CONTROL
  ${NSD_CreateButton} 80% 140u 20% 13u "浏览..."
  Pop $ZHANGCAI_ENV_BROWSE_CONTROL
  ${NSD_OnClick} $ZHANGCAI_ENV_BROWSE_CONTROL ZhangcaiEnvironmentUninstallBrowse
  nsDialogs::Show
FunctionEnd

Function ZhangcaiEnvironmentUninstallBrowse
  nsDialogs::SelectFolderDialog "选择掌财桌面端安装目录" "$ZHANGCAI_ENV_ROOT"
  Pop $0
  ${If} $0 != error
    StrCpy $ZHANGCAI_ENV_ROOT $0
    ${NSD_SetText} $ZHANGCAI_ENV_PATH_CONTROL $ZHANGCAI_ENV_ROOT
  ${EndIf}
FunctionEnd

Function ZhangcaiValidateEnvironmentUninstall
  ${NSD_GetText} $ZHANGCAI_ENV_PATH_CONTROL $ZHANGCAI_ENV_ROOT
  ${If} $ZHANGCAI_ENV_ROOT == ""
    MessageBox MB_ICONSTOP|MB_OK "未指定掌财桌面端安装目录，环境卸载已取消。"
    Abort
  ${EndIf}
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\runtime\environment-version.ini" 0 ZhangcaiEnvironmentUninstallMissing
  IfFileExists "$ZHANGCAI_ENV_ROOT\resources\deepseek-harness\lib\bin.js" 0 ZhangcaiEnvironmentUninstallMissing
  Goto ZhangcaiEnvironmentUninstallValid
  ZhangcaiEnvironmentUninstallMissing:
    MessageBox MB_ICONSTOP|MB_OK "所选目录没有发现掌财运行环境，未执行任何删除。"
    Abort
  ZhangcaiEnvironmentUninstallValid:
FunctionEnd

Page custom ZhangcaiEnvironmentUninstallPageCreate ZhangcaiValidateEnvironmentUninstall
Page instfiles

Section "移除掌财私有运行环境" SEC_ENVIRONMENT_UNINSTALL
  Call ZhangcaiValidateEnvironmentUninstall
  DetailPrint "Environment uninstall: target directory is $ZHANGCAI_ENV_ROOT"
  DetailPrint "Environment uninstall: removing resources\runtime"
  RMDir /r "$ZHANGCAI_ENV_ROOT\resources\runtime"
  DetailPrint "Environment uninstall: removing resources\deepseek-harness"
  RMDir /r "$ZHANGCAI_ENV_ROOT\resources\deepseek-harness"
  DetailPrint "Environment uninstall: removing resources\app\node_modules"
  RMDir /r "$ZHANGCAI_ENV_ROOT\resources\app\node_modules"
  DeleteRegValue HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentRoot"
  DeleteRegValue HKCU "${ZHANGCAI_REG_KEY}" "EnvironmentBaselineVersion"
  DetailPrint "Environment uninstall complete: the main app and data\resource-library were preserved; Windows global runtimes were untouched"
SectionEnd
