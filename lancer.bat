@echo off
rem Lance Audience Lab en local sous Windows : double-cliquer sur ce fichier.
rem
rem Au premier lancement, le script cree l'environnement virtuel .venv et installe
rem les dependances de requirements.txt. Les lancements suivants demarrent
rem directement l'application.
rem
rem Les dependances exigent Python 3.12 ou plus recent. Si la machine n'en dispose
rem pas, le script utilise uv (https://docs.astral.sh/uv/) pour obtenir Python 3.12
rem sans droits administrateur.
chcp 65001 >nul
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\streamlit.exe" goto lancer

echo Premier lancement : préparation de l'environnement (quelques minutes)...
if exist ".venv" rmdir /s /q ".venv"

rem Recherche d'un Python 3.12 ou plus récent deja installe.
set "PYCMD="
py -3.12 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.12"
if not defined PYCMD py -3.13 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.13"
if not defined PYCMD py -3.14 -c "import sys" >nul 2>&1 && set "PYCMD=py -3.14"
if not defined PYCMD python -c "import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)" >nul 2>&1 && set "PYCMD=python"

if defined PYCMD goto avec_python
goto avec_uv

:avec_python
echo Python compatible trouvé.
%PYCMD% -m venv .venv || goto erreur
".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt || goto erreur
goto pret

:avec_uv
echo Aucun Python 3.12 ou plus récent trouvé : utilisation de uv.
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1 || powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex" || goto erreur
uv venv --python 3.12 .venv || goto erreur
uv pip install --python ".venv\Scripts\python.exe" -r requirements.txt || goto erreur

:pret
echo Environnement prêt.

:lancer
echo Démarrage d'Audience Lab sur http://localhost:8501 (fermer cette fenêtre pour arrêter)
".venv\Scripts\streamlit.exe" run app.py --server.headless false
goto fin

:erreur
echo.
echo Le lancement a échoué. Vérifiez la connexion Internet, puis relancez lancer.bat.
echo Application en ligne, sans installation : https://audience-lab.streamlit.app
pause

:fin
endlocal
