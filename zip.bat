@echo off
setlocal

set ZIP_NAME=StefyTube.zip

echo 📦 Creazione archivio %ZIP_NAME% con file essenziali + script .bat e collegamenti .lnk...

REM Elimina zip precedente se esiste
if exist %ZIP_NAME% del %ZIP_NAME%

REM Comprimi usando PowerShell
powershell -Command ^
"Compress-Archive -Path 'app.py','static','templates','requirements.txt','README.md','ffmpeg.exe','build.bat','build_web.bat','zip.bat','StefyTube.lnk','StefyTubeWeb.lnk' -DestinationPath '%ZIP_NAME%' -Force"

echo ✅ Archivio %ZIP_NAME% creato correttamente.
pause
