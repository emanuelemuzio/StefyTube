@echo off
echo Avvio della build di StefyTube...

REM === Build dell'app in sottocartella "StefyTubeApp"
pyinstaller app.py --noconsole --name StefyTubeApp --icon=icon.ico ^
--distpath . --workpath build --specpath .

IF NOT EXIST StefyTubeApp\StefyTubeApp.exe (
    echo Errore: non è stato generato StefyTubeApp.exe
    pause
    exit /b
)

echo 🔁 Spostamento dei file dalla cartella StefyTubeApp alla root...

REM Sposta tutti i file e cartelle dalla cartella build alla root
xcopy /E /Y /I StefyTubeApp\* .

REM Rinomina l'eseguibile da StefyTubeApp.exe → StefyTube.exe
ren StefyTubeApp.exe StefyTube.exe

REM Rimuove cartelle e file inutili
rmdir /s /q StefyTubeApp
rmdir /s /q build
del StefyTubeApp.spec >nul 2>&1

echo Build completata!
echo Puoi ora avviare StefyTube.exe dalla cartella corrente.
pause