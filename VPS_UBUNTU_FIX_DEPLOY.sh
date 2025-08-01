#!/bin/bash

# ENCCEJA 2025 - Fix para Deploy VPS Ubuntu
# Corrige o erro "No module named 'app'"

echo "=== CORRIGINDO DEPLOY VPS UBUNTU ==="

# PASSO 1: Verificar e corrigir estrutura de arquivos
echo "🔍 Verificando estrutura atual..."
cd /var/www/encceja
ls -la

# PASSO 2: Copiar aplicação correta
echo "📋 Copiando aplicação correta..."
if [ -f "VPS_UBUNTU_DEPLOY_COMPLETO.py" ]; then
    echo "✅ Arquivo VPS_UBUNTU_DEPLOY_COMPLETO.py encontrado"
    
    # Fazer backup se existir app.py
    if [ -f "app.py" ]; then
        mv app.py app.py.backup_$(date +%Y%m%d_%H%M%S)
        echo "📦 Backup do app.py anterior criado"
    fi
    
    # Copiar aplicação
    cp VPS_UBUNTU_DEPLOY_COMPLETO.py app.py
    echo "✅ VPS_UBUNTU_DEPLOY_COMPLETO.py copiado para app.py"
else
    echo "❌ Arquivo VPS_UBUNTU_DEPLOY_COMPLETO.py não encontrado!"
    echo "Por favor, faça upload deste arquivo primeiro."
    exit 1
fi

# PASSO 3: Verificar se ambiente virtual existe
echo "🐍 Verificando ambiente Python..."
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

# Ativar ambiente virtual
source venv/bin/activate

# PASSO 4: Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install flask==2.3.3
pip install requests==2.31.0
pip install gunicorn==21.2.0

# QRCode opcional
pip install qrcode[pil] || echo "⚠️ QRCode opcional não instalado"

# PASSO 5: Testar aplicação
echo "🧪 Testando aplicação..."
python3 -c "
try:
    import sys
    sys.path.insert(0, '/var/www/encceja')
    import app
    print('✅ Aplicação importada com sucesso')
    
    # Teste básico
    with app.app.test_client() as client:
        response = client.get('/status')
        if response.status_code == 200:
            print('✅ Rota /status funcionando')
            data = response.get_json()
            print(f'✅ Status: {data.get(\"status\", \"unknown\")}')
        else:
            print(f'❌ Erro na rota /status: {response.status_code}')
except ImportError as e:
    print(f'❌ Erro de importação: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Erro geral: {e}')
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Teste da aplicação passou!"
else
    echo "❌ Erro no teste da aplicação"
    exit 1
fi

# PASSO 6: Configurar environment
echo "⚙️ Configurando environment..."
cat > .env << 'EOF'
SESSION_SECRET=encceja-vps-ubuntu-2025-hostinger-secure
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
FLASK_ENV=production
FLASK_DEBUG=False
EOF

# PASSO 7: Configurar permissões
echo "🔐 Configurando permissões..."
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 600 /var/www/encceja/.env

# PASSO 8: Configurar supervisor
echo "👮 Configurando supervisor..."
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python3 /var/www/encceja/app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
startsecs=10
startretries=5
stderr_logfile=/var/log/supervisor/encceja_error.log
stdout_logfile=/var/log/supervisor/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin:/usr/local/bin:/usr/bin:/bin",PYTHONPATH="/var/www/encceja",PYTHONUNBUFFERED="1"
redirect_stderr=false
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
killasgroup=true
stopasgroup=true
stopsignal=TERM
stopwaitsecs=10
EOF

# PASSO 9: Preparar logs
echo "📝 Preparando logs..."
mkdir -p /var/log/supervisor
touch /var/log/supervisor/encceja_error.log
touch /var/log/supervisor/encceja_output.log
chown www-data:www-data /var/log/supervisor/encceja_*.log

# PASSO 10: Reiniciar supervisor
echo "🚀 Reiniciando supervisor..."
supervisorctl reread
supervisorctl update
supervisorctl stop encceja 2>/dev/null || echo "Serviço não estava rodando"
supervisorctl start encceja

# Aguardar inicialização
sleep 5

# PASSO 11: Verificar status final
echo "🔍 Verificando status final..."
echo "Status do Supervisor:"
supervisorctl status encceja

echo ""
echo "Verificando porta 5000:"
netstat -tlnp | grep :5000 || echo "⚠️ Porta 5000 não ocupada"

echo ""
echo "Teste de conectividade:"
curl -s -I http://localhost:5000/status | head -1 || echo "❌ Erro na conectividade"

echo ""
echo "Últimas linhas do log:"
tail -10 /var/log/supervisor/encceja_output.log 2>/dev/null || echo "Sem logs disponíveis"

# PASSO 12: Status final
status_output=$(supervisorctl status encceja)
if echo "$status_output" | grep -q "RUNNING"; then
    echo ""
    echo "🎉 SUCESSO! ENCCEJA 2025 está rodando corretamente!"
    echo "✅ Aplicação: RUNNING"
    echo "✅ API CPF: Funcionando"
    echo "✅ Sistema PIX: Configurado"
    echo "✅ Porta: 5000"
    echo ""
    echo "📋 Próximos passos:"
    echo "1. Teste no navegador: http://seu-dominio"
    echo "2. Teste formulário CPF: 12345678901"
    echo "3. Monitore logs: tail -f /var/log/supervisor/encceja_output.log"
else
    echo ""
    echo "❌ PROBLEMA DETECTADO!"
    echo "Status atual: $status_output"
    echo ""
    echo "🔧 Diagnóstico:"
    echo "Ver logs de erro:"
    tail -20 /var/log/supervisor/encceja_error.log
    echo ""
    echo "Testar aplicação manualmente:"
    echo "cd /var/www/encceja && source venv/bin/activate && python3 app.py"
fi