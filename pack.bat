Pyinstaller -i=".\icon\icon.ico" -F main.py
Python packer.py
rd /s /q .\dist
rd /s /q .\build
del .\main.spec
pause