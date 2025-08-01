#!/bin/bash
# VPS - Setup automático com ambiente virtual para resolver "externally-managed-environment"

echo "🔧 ENCCEJA VPS - Setup com Ambiente Virtual"
echo "==========================================="

# Verificar se estamos no diretório correto
if [ ! -d "/var/www/encceja" ]; then
    echo "📁 Criando diretório /var/www/encceja..."
    mkdir -p /var/www/encceja
fi

cd /var/www/encceja

# Criar ambiente virtual
echo "🐍 Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual  
echo "⚡ Ativando ambiente virtual..."
source venv/bin/activate

# Verificar se ativou corretamente
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Ambiente virtual ativo: $VIRTUAL_ENV"
else
    echo "❌ Erro ao ativar ambiente virtual"
    exit 1
fi

# Instalar dependências
echo "📦 Instalando dependências..."
pip install --upgrade pip
pip install flask gunicorn requests qrcode[pil] python-dotenv

# Verificar instalações
echo "🔍 Verificando instalações..."
python -c "import flask; print('✅ Flask:', flask.__version__)" || echo "❌ Flask falhou"
python -c "import requests; print('✅ Requests: OK')" || echo "❌ Requests falhou"  
python -c "import qrcode; print('✅ QRCode: OK')" || echo "❌ QRCode falhou"

# Criar aplicação de teste
echo "🧪 Criando aplicação de teste..."
cat > app.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask, redirect, url_for

app = Flask(__name__)
app.secret_key = "vps-test-key"

@app.route('/')
def home():
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENCCEJA 2025 - VPS Funcionando</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background: #f0f8ff; margin: 20px 0; }
            .success { color: green; font-weight: bold; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 ENCCEJA 2025</h1>
            <h2>Sistema VPS Funcionando!</h2>
        </div>
        
        <div class="content">
            <div class="success">✅ AMBIENTE VIRTUAL CONFIGURADO COM SUCESSO!</div>
            
            <h3>Status do Sistema:</h3>
            <ul>
                <li>✅ Python: Funcionando</li>
                <li>✅ Flask: Instalado no venv</li>
                <li>✅ Ambiente Virtual: Ativo</li>
                <li>✅ VPS: Conectado</li>
                <li>✅ Nginx: Proxy configurado</li>
            </ul>
            
            <h3>Próximos Passos:</h3>
            <ol>
                <li>Upload da aplicação ENCCEJA completa</li>
                <li>Configurar templates e static files</li>
                <li>Ativar APIs reais (CPF + WitePay)</li>
                <li>Testar funnel completo</li>
            </ol>
        </div>
    </body>
    </html>
    """

if __name__ == '__main__':
    print("🚀 Iniciando ENCCEJA VPS na porta 5000...")
    print("🔗 Acesse via seu domínio")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Configurar Supervisor
echo "⚙️ Configurando Supervisor..."
cat > /etc/supervisor/conf.d/encceja.conf << EOF
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app.py
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PYTHONPATH="/var/www/encceja",PYTHONUNBUFFERED="1"
EOF

# Recarregar Supervisor
echo "🔄 Recarregando Supervisor..."
supervisorctl reread
supervisorctl update  
supervisorctl start encceja

# Configurar Nginx se não existir
if [ ! -f "/etc/nginx/sites-available/encceja" ]; then
    echo "🌐 Configurando Nginx..."
    cat > /etc/nginx/sites-available/encceja << 'EOF'
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

    # Ativar site
    ln -sf /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    nginx -t && systemctl reload nginx
fi

echo ""
echo "✅ SETUP COMPLETO COM VENV!"
echo "============================"
echo ""
echo "📊 Status dos Serviços:"
supervisorctl status encceja
echo "Nginx:" $(systemctl is-active nginx)

echo ""
echo "🧪 Teste Local:"
sleep 2
curl -I http://127.0.0.1:5000/ 2>/dev/null | head -1

echo ""
echo "🎯 PRÓXIMOS PASSOS:"
echo "1. Acesse seu domínio para ver se funciona"
echo "2. Se OK, faça upload da aplicação ENCCEJA completa"
echo "3. Execute: supervisorctl restart encceja"
echo "4. Sistema pronto para produção!"

echo ""
echo "📁 Arquivos importantes:"
echo "- App: /var/www/encceja/app.py"
echo "- Venv: /var/www/encceja/venv/"  
echo "- Logs: /var/log/encceja.log"