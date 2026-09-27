@echo off
rem 打包《贝娜的量角器》
rem   pack.bat           -> Qt 版（onedir + PySide6，推荐分发形态）
rem   pack.bat legacy    -> 旧 tkinter 版（onefile，体积小）
rem 产物在 output\ 目录；tables/ 数据不打进包，用户首次启动时自行下载。
setlocal
cd /d "%~dp0"

set "PYEXE=python"
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"

set "MODE="
if /i "%~1"=="legacy" set "MODE=--legacy"
if /i "%~1"=="tk" set "MODE=--legacy"

"%PYEXE%" "tools\launch.py" --pack %MODE%
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [pack.bat] Build failed. Press any key to exit...
    pause >nul
    exit /b 1
)

if exist ".\build" rd /s /q ".\build"
if exist ".\BenaProtractor.spec" del /q ".\BenaProtractor.spec"
echo.
echo [pack.bat] Done. See the output folder.
pause
endlocal
exit /b 0
