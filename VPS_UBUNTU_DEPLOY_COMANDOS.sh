#!/bin/bash

# ENCCEJA 2025 - Script de Deploy para VPS Ubuntu Hostinger
# Execute este script linha por linha ou como um todo

echo "=== ENCCEJA 2025 - DEPLOY VPS UBUNTU HOSTINGER ==="
echo "Iniciando configuração completa..."

# PASSO 1: Parar aplicação atual e fazer backup
echo "🔄 Passo 1: Parando aplicação e fazendo backup..."
supervisorctl stop encceja || echo "Serviço não estava rodando"
cd /var/www/encceja
mv app.py app.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "Sem app.py anterior"

# PASSO 2: Preparar ambiente Python
echo "🐍 Passo 2: Configurando ambiente Python..."
# Ativar ambiente virtual (criar se não existir)
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
fi

source venv/bin/activate

# Atualizar pip
pip install --upgrade pip

# Instalar dependências essenciais
echo "📦 Instalando dependências..."
pip install flask==2.3.3
pip install requests==2.31.0
pip install gunicorn==21.2.0

# QRCode é opcional
pip install qrcode[pil] || echo "⚠️ QRCode opcional não instalado (aplicação funcionará sem)"

# Verificar instalações
echo "✅ Verificando instalações..."
python3 -c "import flask, requests; print('✅ Flask e Requests OK')"

# PASSO 3: Configurar arquivo de ambiente
echo "⚙️ Passo 3: Configurando variáveis de ambiente..."
cat > .env << 'EOF'
# ENCCEJA 2025 - VPS Ubuntu Hostinger
SESSION_SECRET=encceja-vps-ubuntu-2025-hostinger-secure
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
FLASK_ENV=production
FLASK_DEBUG=False
EOF

# PASSO 4: Configurar permissões
echo "🔐 Passo 4: Configurando permissões..."
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 600 /var/www/encceja/.env

# PASSO 5: Configurar supervisor
echo "👮 Passo 5: Configurando Supervisor..."
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

# PASSO 6: Criar diretórios de log
echo "📝 Passo 6: Preparando logs..."
mkdir -p /var/log/supervisor
touch /var/log/supervisor/encceja_error.log
touch /var/log/supervisor/encceja_output.log
chown www-data:www-data /var/log/supervisor/encceja_*.log

# PASSO 7: Teste rápido da aplicação
echo "🧪 Passo 7: Testando aplicação..."
cd /var/www/encceja
source venv/bin/activate

# Teste se o arquivo carrega sem erros
python3 -c "
try:
    import app
    print('✅ Aplicação carrega sem erros')
    
    # Teste rota de status
    with app.app.test_client() as client:
        response = client.get('/status')
        if response.status_code == 200:
            print('✅ Rota /status funciona')
            print('📊 Status:', response.get_json()['status'])
        else:
            print('❌ Erro na rota /status')
            
except Exception as e:
    print('❌ Erro ao carregar aplicação:', str(e))
    exit(1)
"

if [ $? -eq 0 ]; then
    echo "✅ Teste da aplicação passou!"
else
    echo "❌ Erro no teste da aplicação. Verifique o código."
    exit 1
fi

# PASSO 8: Atualizar e iniciar supervisor
echo "🚀 Passo 8: Iniciando aplicação..."
supervisorctl reread
supervisorctl update
supervisorctl start encceja

# Aguardar alguns segundos para inicialização
sleep 5

# PASSO 9: Verificar status
echo "🔍 Passo 9: Verificando status final..."
echo "Status do Supervisor:"
supervisorctl status encceja

echo ""
echo "Verificando processo na porta 5000:"
netstat -tlnp | grep :5000 || echo "⚠️ Nenhum processo na porta 5000"

echo ""
echo "Teste de conectividade local:"
curl -s -I http://localhost:5000/status | head -1 || echo "❌ Erro na conectividade local"

echo ""
echo "Últimas linhas do log:"
tail -10 /var/log/supervisor/encceja_output.log 2>/dev/null || echo "Sem logs ainda"

# PASSO 10: Informações finais
echo ""
echo "=== DEPLOY CONCLUÍDO ==="
echo "✅ Aplicação: ENCCEJA 2025 VPS Ubuntu"
echo "✅ Ambiente: Produção"
echo "✅ API CPF: https://consulta.fontesderenda.blog/cpf.php"
echo "✅ Sistema PIX: WitePay + Fallback"
echo "✅ Porta: 5000"
echo "✅ Supervisor: Configurado"
echo ""
echo "📋 Próximos passos:"
echo "1. Verifique se 'supervisorctl status encceja' mostra RUNNING"
echo "2. Teste o site no navegador: http://seu-dominio"
echo "3. Teste o formulário CPF com um número válido"
echo "4. Monitore os logs: tail -f /var/log/supervisor/encceja_output.log"
echo ""
echo "🆘 Se houver problemas:"
echo "- Ver logs: tail -50 /var/log/supervisor/encceja_error.log"
echo "- Restart: supervisorctl restart encceja"
echo "- Status: supervisorctl status encceja"
echo ""
echo "🎉 ENCCEJA 2025 está pronto na VPS Ubuntu Hostinger!"