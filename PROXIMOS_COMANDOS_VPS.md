# ✅ PRÓXIMOS COMANDOS - VPS UBUNTU

Você já executou com sucesso:
```bash
apt install python3 python3-pip python3-venv nginx supervisor git -y
```

## **AGORA EXECUTE:**

### 1. Criar o diretório e ambiente virtual:
```bash
mkdir -p /var/www/encceja
cd /var/www/encceja
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar pacotes Python:
```bash
pip install --upgrade pip
pip install Flask==3.0.0 gunicorn==21.2.0 requests==2.31.0 qrcode[pil]==7.4.2 python-dotenv==1.0.0 Pillow==10.1.0
```

### 3. Criar arquivo de ambiente:
```bash
cat > .env << EOF
SESSION_SECRET=$(openssl rand -hex 32)
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
CPF_API_TOKEN=1285fe4s-e931-4071-a848-3fac8273c55a
FLASK_ENV=production
EOF
```

### 4. Criar configuração Gunicorn:
```bash
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 30
preload_app = True
EOF
```

### 5. Configurar Supervisor:
```bash
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
```

### 6. Configurar Nginx:
```bash
cat > /etc/nginx/sites-available/encceja << EOF
server {
    listen 80;
    server_name _;
    
    location /static/ {
        alias /var/www/encceja/static/;
        expires 30d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
```

### 7. Copiar arquivos do projeto:
```bash
# Copie app.py, templates/ e static/ para /var/www/encceja/
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/
```

### 8. Definir permissões e iniciar:
```bash
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
supervisorctl reread
supervisorctl update
systemctl restart nginx
supervisorctl start encceja
```

### 9. Verificar se funcionou:
```bash
curl -I http://localhost:5000
```

Deve retornar `HTTP/1.1 200 OK`

**Execute esses comandos em sequência e o sistema estará funcionando!**