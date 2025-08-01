#!/bin/bash
# VPS - Setup completo ENCCEJA com todas as dependências

echo "🚀 ENCCEJA VPS - Setup Completo"
echo "================================"

# Atualizar sistema
echo "📦 Atualizando sistema..."
apt update

# Instalar Python e pip se não existir
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    apt install python3 python3-pip -y
fi

# Instalar dependências Python
echo "📚 Instalando dependências Python..."
pip3 install flask gunicorn requests qrcode[pil] python-dotenv

# Criar diretório se não existir
echo "📁 Criando estrutura de diretórios..."
mkdir -p /var/www/encceja
cd /var/www/encceja

# Criar requirements.txt
echo "📄 Criando requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==2.3.3
gunicorn==21.2.0
requests==2.31.0
qrcode[pil]==7.4.2
python-dotenv==1.0.0
Pillow==10.0.0
EOF

# Instalar requirements
pip3 install -r requirements.txt

# Criar aplicação de teste
echo "🧪 Criando aplicação de teste..."
cat > test_app.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return """
    <h1>✅ ENCCEJA VPS FUNCIONANDO!</h1>
    <p>Python: OK</p>
    <p>Flask: OK</p>
    <p>Dependências: Instaladas</p>
    <hr>
    <p>Sistema pronto para ENCCEJA</p>
    """

if __name__ == '__main__':
    print("🌐 Iniciando teste na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Tornar executável
chmod +x test_app.py

# Testar aplicação
echo "🔍 Testando aplicação..."
python3 -c "import flask; print('✅ Flask:', flask.__version__)"
python3 -c "import requests; print('✅ Requests: OK')"
python3 -c "import qrcode; print('✅ QRCode: OK')"

# Configurar Supervisor
echo "⚙️ Configurando Supervisor..."
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=python3 /var/www/encceja/test_app.py
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PYTHONUNBUFFERED="1"
EOF

# Recarregar Supervisor
supervisorctl reread
supervisorctl update
supervisorctl start encceja

# Configurar Nginx
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
nginx -t
systemctl reload nginx

echo ""
echo "✅ SETUP COMPLETO!"
echo "===================="
echo "📍 Aplicação: /var/www/encceja"
echo "🔗 Teste: curl http://127.0.0.1:5000/"
echo "🌐 Acesse via seu domínio"
echo ""
echo "📊 Status dos serviços:"
supervisorctl status encceja
systemctl is-active nginx

echo ""
echo "🎯 Para usar aplicação real:"
echo "1. Upload app.py completo"
echo "2. supervisorctl restart encceja"
echo "3. Pronto!"