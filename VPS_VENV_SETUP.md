# VPS - Configuração com Ambiente Virtual

## Problema: "externally-managed-environment" 
O sistema Python da VPS não permite instalação direta via pip. Solução: usar ambiente virtual.

## Setup Completo com VENV

### 1. Criar ambiente virtual
```bash
cd /var/www/encceja
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependências no ambiente virtual
```bash
# Agora pip funciona dentro do venv
pip install flask
pip install gunicorn  
pip install requests
pip install qrcode[pil]
pip install python-dotenv
```

### 3. Verificar instalação
```bash
# Dentro do venv ativado
python -c "import flask; print('Flask OK')"
python -c "import requests; print('Requests OK')"
```

### 4. Criar requirements.txt
```bash
cat > requirements.txt << 'EOF'
Flask==2.3.3
gunicorn==21.2.0
requests==2.31.0
qrcode[pil]==7.4.2
python-dotenv==1.0.0
Pillow==10.0.0
EOF

pip install -r requirements.txt
```

### 5. Configurar Supervisor com VENV
```bash
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
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
```

### 6. Recarregar Supervisor
```bash
supervisorctl reread
supervisorctl update
supervisorctl start encceja
supervisorctl status encceja
```

### 7. Teste final
```bash
# Verificar se aplicação responde
curl http://127.0.0.1:5000/

# Ver logs se necessário
tail -f /var/log/encceja.log
```

## Comandos Completos em Sequência

Execute este bloco completo na VPS:
```bash
cd /var/www/encceja && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install flask gunicorn requests qrcode[pil] python-dotenv && \
python -c "import flask; print('✅ Flask instalado no venv')" && \
echo "🎯 Ambiente virtual configurado com sucesso!"
```

## Configuração Supervisor Final
```bash
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app.py
directory=/var/www/encceja
user=root
autostart=true  
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
EOF

supervisorctl reread && supervisorctl update && supervisorctl start encceja
```

## Verificação
```bash
supervisorctl status encceja
curl -I http://127.0.0.1:5000/
```

Depois disso o erro 502 Bad Gateway deve ser resolvido!