#!/bin/bash
# Instalador para macOS. Dê dois cliques (ou rode: bash instalar_mac.command).
cd "$(dirname "$0")" || exit 1
echo "=== Instalando o Coletor de Partidas TCG Live ==="
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 não encontrado. Instale em https://www.python.org/downloads/"
  read -r -p "Enter para sair"; exit 1
fi
python3 -m venv .venv || { echo "Não consegui criar o ambiente .venv"; exit 1; }
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt || { echo "Falha ao instalar as dependências."; exit 1; }
read -r -p "Instalar também o modo automático (reconhece e clica nos botões do jogo)? [s/N] " AUTO
if [[ "$AUTO" =~ ^[sS]$ ]]; then
  pip install -r requirements-auto.txt
  echo "No macOS, permita o Terminal em Ajustes > Privacidade e Segurança > Gravação de Tela e Acessibilidade."
fi
chmod +x iniciar_mac.command
echo "Pronto! Para abrir o programa, use iniciar_mac.command"
