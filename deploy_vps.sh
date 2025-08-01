#!/bin/bash

# Script de Deploy Automático - ENCCEJA Ubuntu VPS
# Execute como root: bash deploy_vps.sh

echo "=== INICIANDO DEPLOY ENCCEJA VPS ==="

# 1. Atualizar sistema
echo "Atualizando sistema..."
apt update && apt upgrade -y

# 2. Instalar dependências
echo "Instalando dependências..."
apt install python3.11 python3.11-pip python3.11-venv nginx supervisor git certbot python3-certbot-nginx -y

# 3. Criar diretório do projeto
echo "Criando diretório do projeto..."
mkdir -p /var/www/encceja
cd /var/www/encceja

# 4. Configurar ambiente Python
echo "Configurando ambiente Python..."
python3.11 -m venv venv
source venv/bin/activate

# 5. Instalar pacotes Python
echo "Instalando pacotes Python..."
pip install Flask==3.0.0 gunicorn==21.2.0 requests==2.31.0 qrcode[pil]==7.4.2 python-dotenv==1.0.0 Pillow==10.1.0

# 6. Criar arquivo .env
echo "Configurando variáveis de ambiente..."
cat > .env << EOF
SESSION_SECRET=$(openssl rand -hex 32)
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
CPF_API_TOKEN=1285fe4s-e931-4071-a848-3fac8273c55a
FLASK_ENV=production
EOF

chmod 600 .env
chown www-data:www-data .env

# 7. Criar configuração do Gunicorn
echo "Configurando Gunicorn..."
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF

# 8. Configurar Supervisor
echo "Configurando Supervisor..."
cat > /etc/supervisor/conf.d/encceja.conf << EOF
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --config gunicorn.conf.py app:app
directory=/var/www/encceja
user=www-data
group=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PATH="/var/www/encceja/venv/bin"
EOF

# 9. Configurar Nginx
echo "Configurando Nginx..."
cat > /etc/nginx/sites-available/encceja << EOF
server {
    listen 80;
    server_name _;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /var/www/encceja/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Ativar site
ln -sf /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# 10. Configurar firewall
echo "Configurando firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# 11. Definir permissões
echo "Definindo permissões..."
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja

# 12. Iniciar serviços
echo "Iniciando serviços..."
supervisorctl reread
supervisorctl update
nginx -t && systemctl restart nginx
systemctl enable nginx
supervisorctl start encceja

echo "=== DEPLOY CONCLUÍDO ==="
echo "Sistema disponível em: http://$(curl -s ifconfig.me)"
echo "Logs: tail -f /var/log/encceja.log"
echo "Status: supervisorctl status encceja"