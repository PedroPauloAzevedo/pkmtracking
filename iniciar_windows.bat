@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Rode primeiro o instalar_windows.bat
  pause
  exit /b 1
)
title Coletor de Partidas TCG Live
".venv\Scripts\python.exe" app.py
pause
