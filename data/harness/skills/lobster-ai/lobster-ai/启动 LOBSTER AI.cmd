@echo off
setlocal
cd /d "%~dp0"

set "LOBSTER_PY=C:\Users\Administrator\AppData\Local\Programs\Python\Python313\python.exe"
if exist "%LOBSTER_PY%" goto :run

where python >nul 2>nul
if not errorlevel 1 (
  set "LOBSTER_PY=python"
  goto :run
)

where py >nul 2>nul
if not errorlevel 1 (
  set "LOBSTER_PY=py -3"
  goto :run
)

echo [ERROR] Python 3 was not found.
pause
exit /b 1

:run
%LOBSTER_PY% "scripts\lobster_cli.py" launch
if errorlevel 1 (
  echo.
  echo [ERROR] LOBSTER AI failed to start. Review the error above.
  pause
)

