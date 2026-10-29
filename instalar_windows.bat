@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === Instalando o Coletor de Partidas TCG Live ===
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY (
  echo Python nao encontrado.
  echo Instale em https://www.python.org/downloads/ e marque "Add python.exe to PATH".
  pause
  exit /b 1
)
%PY% -m venv .venv || (echo Nao consegui criar o ambiente .venv & pause & exit /b 1)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Falha ao instalar as dependencias. & pause & exit /b 1)
echo.
set /p AUTO=Instalar tambem o modo automatico (reconhece e clica nos botoes do jogo)? [s/N]
if /i "%AUTO%"=="s" pip install -r requirements-auto.txt
echo.
echo Pronto! Para abrir o programa, use iniciar_windows.bat
pause
