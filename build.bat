@echo off
echo Pulizia cartelle dist e build...
rmdir /s /q dist
rmdir /s /q build
del main.spec

echo Avvio PyInstaller...
pyinstaller --onefile --noconsole --add-data "static;static" --add-data "templates;templates" --add-data "ffmpeg.exe;." app.py

echo Build completata. EXE in dist\
pause
