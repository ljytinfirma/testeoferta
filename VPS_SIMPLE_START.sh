#!/bin/bash
# VPS - Script para iniciar aplicação ENCCEJA manualmente

echo "🚀 Iniciando ENCCEJA VPS..."

# Ir para diretório
cd /var/www/encceja

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências se necessário
pip install flask gunicorn requests qrcode[pil] 2>/dev/null

# Iniciar aplicação
echo "📍 Iniciando Flask na porta 5000..."
export PYTHONUNBUFFERED=1
python app.py

# Se Flask falhar, tentar Gunicorn
if [ $? -ne 0 ]; then
    echo "⚡ Tentando Gunicorn..."
    gunicorn --bind 0.0.0.0:5000 --workers 1 app:app
fi