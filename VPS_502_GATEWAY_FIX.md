# VPS - Correção Erro 502 Bad Gateway

## 🚨 Problema Identificado
**502 Bad Gateway** = Nginx não consegue conectar com a aplicação Flask

## ⚡ Solução Rápida

### 1. Conectar na VPS
```bash
ssh root@SEU_IP_VPS
```

### 2. Verificar Status dos Serviços
```bash
# Verificar se supervisor está rodando
systemctl status supervisor

# Verificar se nginx está rodando  
systemctl status nginx

# Verificar se aplicação está rodando
supervisorctl status encceja
```

### 3. Verificar Aplicação Flask
```bash
cd /var/www/encceja

# Testar se aplicação responde local
curl -I http://127.0.0.1:5000/
# Deve retornar: HTTP/1.1 302 FOUND

# Se não responder, verificar logs
tail -f /var/log/encceja.log
```

### 4. Corrigir Aplicação se Não Estiver Rodando
```bash
# Parar supervisor
supervisorctl stop encceja

# Testar aplicação manual
cd /var/www/encceja
source venv/bin/activate
python app.py

# Se der erro, instalar dependências
pip install flask requests qrcode[pil] gunicorn python-dotenv
```

### 5. Verificar Arquivo app.py
```bash
# Verificar se arquivo existe
ls -la /var/www/encceja/app.py

# Se não existir, criar
cat > /var/www/encceja/app.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import logging
from flask import Flask, render_template, redirect, url_for

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = "test-secret-key"

@app.route('/')
def index():
    app.logger.info("Acesso à rota /")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    app.logger.info("Acesso à rota /inscricao")
    return "<h1>ENCCEJA 2025 - Sistema Funcionando!</h1><p>Aplicação rodando corretamente na VPS</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF
```

### 6. Reiniciar Serviços
```bash
# Reiniciar supervisor
supervisorctl reread
supervisorctl update
supervisorctl restart encceja

# Verificar se subiu
supervisorctl status encceja

# Testar conexão
curl -I http://127.0.0.1:5000/

# Reiniciar nginx
systemctl reload nginx
```

### 7. Verificar Configuração Nginx
```bash
# Testar configuração
nginx -t

# Ver configuração atual
cat /etc/nginx/sites-available/encceja

# Se não existir, criar
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
```

## 🔍 Diagnóstico Detalhado

### Verificar Logs
```bash
# Log da aplicação
tail -f /var/log/encceja.log

# Log do nginx
tail -f /var/log/nginx/error.log

# Log do supervisor
tail -f /var/log/supervisor/supervisord.log
```

### Verificar Portas
```bash
# Ver o que está rodando na porta 5000
ss -tlnp | grep :5000

# Ver processos python
ps aux | grep python

# Ver processos gunicorn
ps aux | grep gunicorn
```

## 🎯 Teste Final

### 1. Teste Local na VPS
```bash
curl http://127.0.0.1:5000/
# Deve retornar HTML ou redirecionamento
```

### 2. Teste via Domínio
Acesse: `http://seu-dominio.com`

Deve exibir: "ENCCEJA 2025 - Sistema Funcionando!"

## ⚠️ Problemas Comuns

### Python não encontrado
```bash
which python3
# Se não retornar caminho, instalar:
apt install python3 python3-pip python3-venv
```

### Dependências em falta
```bash
cd /var/www/encceja
source venv/bin/activate
pip install flask gunicorn
```

### Permissões incorretas
```bash
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
```

### Firewall bloqueando
```bash
ufw allow 80
ufw allow 443
ufw status
```

## 📞 Verificação Rápida

Execute este comando na VPS para teste completo:
```bash
echo "=== TESTE COMPLETO VPS ===" && \
echo "1. Status Supervisor:" && supervisorctl status && \
echo "2. Status Nginx:" && systemctl is-active nginx && \
echo "3. Teste Local:" && curl -I http://127.0.0.1:5000/ && \
echo "4. Processos Python:" && ps aux | grep python | head -3 && \
echo "=== FIM TESTE ==="
```

Se todos os testes passarem, o site deve funcionar no domínio!