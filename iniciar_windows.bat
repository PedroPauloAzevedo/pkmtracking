@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Rode primeiro o instalar_windows.bat
  pause
  exit /b 1
)
rem Com o icone perto do relogio disponivel, abre sem janela preta.
".venv\Scripts\python.exe" -c "import pystray, PIL" >nul 2>nul
if not errorlevel 1 if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" app.py
  exit /b 0
)
title Coletor de Partidas TCG Live
".venv\Scripts\python.exe" app.py --janela
pause
