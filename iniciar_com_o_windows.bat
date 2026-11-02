@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Rode primeiro o instalar_windows.bat
  pause
  exit /b 1
)
rem Cria um atalho na pasta "Inicializar" do Windows que abre o programa sem janela.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetFolderPath('Startup'); $s=(New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $p 'Coletor TCG Live.lnk')); $s.TargetPath=(Resolve-Path '.venv\Scripts\pythonw.exe').Path; $s.Arguments='app.py --sem-navegador'; $s.WorkingDirectory=(Get-Location).Path; $s.IconLocation=(Resolve-Path 'web\icone.ico').Path; $s.Save()"
if errorlevel 1 (
  echo Nao consegui criar o atalho.
  pause
  exit /b 1
)
echo Pronto! O coletor vai abrir sozinho (sem janela) sempre que o Windows iniciar.
echo Ele aparece como um icone perto do relogio. Para desfazer, use nao_iniciar_com_o_windows.bat
start "" ".venv\Scripts\pythonw.exe" app.py --sem-navegador
pause
