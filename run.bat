@echo off
:START
python main.py
if %ERRORLEVEL% NEQ 0 goto ERROR

:FINE
goto END

:ERROR
echo 发现错误，请点击以重复运行？
pause >nul
goto START

: END
EXIT