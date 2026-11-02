@echo off
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "$f=Join-Path ([Environment]::GetFolderPath('Startup')) 'Coletor TCG Live.lnk'; if (Test-Path $f) { Remove-Item $f; 'Removido: o coletor nao abre mais com o Windows.' } else { 'O coletor nao estava configurado para abrir com o Windows.' }"
echo Se ele estiver rodando agora, feche pelo icone perto do relogio (botao direito > Sair).
pause
