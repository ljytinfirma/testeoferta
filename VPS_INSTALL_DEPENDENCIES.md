# VPS - Instalação de Dependências ENCCEJA

## Execute estes comandos na VPS para corrigir o erro Flask

### 1. Instalar Flask e dependências
```bash
pip install flask
pip install gunicorn
pip install requests
pip install qrcode[pil]
pip install python-dotenv
```

### 2. Ou instalar tudo de uma vez
```bash
pip install flask gunicorn requests qrcode[pil] python-dotenv
```

### 3. Verificar instalação
```bash
python3 -c "import flask; print('Flask instalado:', flask.__version__)"
python3 -c "import requests; print('Requests OK')"
python3 -c "import qrcode; print('QRCode OK')"
```

### 4. Criar requirements.txt na VPS
```bash
cat > /var/www/encceja/requirements.txt << 'EOF'
Flask==2.3.3
gunicorn==21.2.0
requests==2.31.0
qrcode[pil]==7.4.2
python-dotenv==1.0.0
Pillow==10.0.0
EOF
```

### 5. Instalar via requirements
```bash
cd /var/www/encceja
pip install -r requirements.txt
```

### 6. Teste após instalação
```bash
python3 VPS_MINIMAL_TEST.py
```

### 7. Se funcionar, configurar Supervisor
```bash
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=python3 /var/www/encceja/app.py
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PYTHONUNBUFFERED="1"
EOF

supervisorctl reread
supervisorctl update
supervisorctl start encceja
```

### 8. Verificar funcionamento
```bash
supervisorctl status encceja
curl http://127.0.0.1:5000/
```

## Script de Instalação Completa

Execute este bloco completo:
```bash
echo "🔧 Instalando dependências ENCCEJA..." && \
pip install flask gunicorn requests qrcode[pil] python-dotenv && \
echo "✅ Dependências instaladas" && \
python3 -c "import flask; print('Flask:', flask.__version__)" && \
echo "🚀 Pronto para rodar aplicação"
```