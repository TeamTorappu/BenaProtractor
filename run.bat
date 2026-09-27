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
"%PYEXE%" "tools\launch.py" %UIARG%
if %ERRORLEVEL% NEQ 0 goto ERROR
goto END

:ERROR
echo.
echo [run.bat] The program exited with an error. Press any key to retry...
pause >nul
goto START

:END
endlocal
exit /b 0
