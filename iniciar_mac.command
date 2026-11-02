#!/bin/bash
cd "$(dirname "$0")" || exit 1
if [ ! -x ".venv/bin/python" ]; then
  echo "Rode primeiro o instalar_mac.command"; read -r -p "Enter para sair"; exit 1
fi
.venv/bin/python app.py
