@echo off
rem Launch Bena Protractor
rem   default : project .venv python + Qt (PySide6) UI
rem   fallback: if PySide6 is missing it falls back to the old tkinter UI
rem   run.bat tk  -> force the tkinter UI
setlocal
cd /d "%~dp0"

set "PYEXE=python"
if exist ".venv\Scripts\python.exe" set "PYEXE=.venv\Scripts\python.exe"

set "UIARG="
if /i "%~1"=="tk" set "UIARG=--ui tk"

:START
"%PYEXE%" "main.py" %UIARG%
if %ERRORLEVEL% NEQ 0 goto ERROR
goto END

:ERROR
echo.
echo [启动器] 发现错误。按任意键尝试重复运行...
pause >nul
goto START

:END
endlocal
exit /b 0
