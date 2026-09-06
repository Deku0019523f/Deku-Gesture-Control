@echo off
REM Construit l'executable Windows DekuGestureControl.exe (spec section 31).
REM A executer DEPUIS LA RACINE DU PROJET, sur Windows, apres avoir active
REM l'environnement virtuel et installe les dependances :
REM
REM   python -m venv venv
REM   venv\Scripts\activate
REM   pip install -r requirements.txt
REM   pip install pyinstaller

echo ============================================
echo   Construction de Deku Gesture Control .exe
echo ============================================

where pyinstaller >nul 2>nul
if errorlevel 1 (
    echo [ERREUR] PyInstaller n'est pas installe. Lancez : pip install pyinstaller
    exit /b 1
)

pyinstaller packaging\deku_gesture_control.spec --noconfirm

if errorlevel 1 (
    echo [ERREUR] La construction a echoue. Voir le message ci-dessus.
    exit /b 1
)

echo.
echo Termine ! Executable disponible dans :
echo   dist\DekuGestureControl\DekuGestureControl.exe
echo.
echo Vous pouvez copier tout le dossier dist\DekuGestureControl sur
echo n'importe quel PC Windows : aucune installation de Python requise.
echo.
pause
