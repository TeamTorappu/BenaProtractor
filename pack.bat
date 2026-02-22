Pyinstaller -i=".\icon\icon.ico" -F main.py
pause
Python Packer.py
rd /s /q .\dist
rd /s /q .\build
del .\main.spec
pause