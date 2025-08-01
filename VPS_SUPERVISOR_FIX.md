# VPS - Correção Supervisor "spawn error"

## 🚨 Problema: Supervisor não consegue iniciar aplicação

Execute estes comandos na VPS para corrigir:

### 1. Parar o serviço com erro
```bash
supervisorctl stop encceja
```

### 2. Verificar estrutura de arquivos
```bash
cd /var/www/encceja
ls -la
# Deve mostrar: app.py, venv/, templates/, static/
```

### 3. Criar ambiente virtual se não existir
```bash
cd /var/www/encceja
python3 -m venv venv
source venv/bin/activate
pip install flask gunicorn requests qrcode[pil]
```

### 4. Testar aplicação manual
```bash
cd /var/www/encceja
source venv/bin/activate
python app.py
# Deve mostrar: "Running on http://0.0.0.0:5000"
# Pressione Ctrl+C para parar
```

### 5. Criar configuração correta do Supervisor
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

### 7. Se ainda der erro, usar Gunicorn
```bash
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 1 app:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
stderr_logfile=/var/log/encceja_error.log
EOF

supervisorctl reread
supervisorctl update
supervisorctl start encceja
```

### 8. Verificar logs se der erro
```bash
tail -f /var/log/encceja.log
tail -f /var/log/encceja_error.log
```

### 9. Teste final
```bash
# Verificar se aplicação responde
curl http://127.0.0.1:5000/

# Status do supervisor
supervisorctl status encceja
```

## Comandos Rápidos de Teste

Execute este bloco completo:
```bash
cd /var/www/encceja && \
echo "=== TESTE ESTRUTURA ===" && \
ls -la && \
echo "=== TESTE PYTHON ===" && \
which python3 && \
echo "=== TESTE VENV ===" && \
source venv/bin/activate && \
python --version && \
echo "=== TESTE FLASK ===" && \
python -c "import flask; print('Flask OK')" && \
echo "=== RESTART SUPERVISOR ===" && \
supervisorctl restart encceja && \
supervisorctl status encceja
```