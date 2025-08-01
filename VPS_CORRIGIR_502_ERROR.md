# Corrigir Erro 502 Bad Gateway - ENCCEJA VPS

## 🚨 DIAGNÓSTICO DO PROBLEMA

Com base nas imagens fornecidas:
- ✗ Supervisor mostra: `encceja: stopped`
- ✗ Erro ao tentar restart: `ERROR (spawn error)`
- ✗ Nginx retorna: `502 Bad Gateway`

## 🔧 SOLUÇÕES PASSO A PASSO

### PASSO 1: Verificar logs de erro

```bash
# Ver logs de erro da aplicação
tail -50 /var/log/encceja_error.log

# Ver logs de saída
tail -50 /var/log/encceja_output.log

# Ver logs do supervisor
tail -50 /var/log/supervisor/supervisord.log
```

### PASSO 2: Verificar estrutura de arquivos

```bash
# Verificar se os arquivos existem
ls -la /var/www/encceja/
ls -la /var/www/encceja/app.py
ls -la /var/www/encceja/venv/

# Verificar permissões
ls -la /var/www/encceja/app.py
```

### PASSO 3: Testar aplicação manualmente

```bash
# Ativar ambiente virtual
cd /var/www/encceja
source venv/bin/activate

# Testar se o Python consegue executar
python app.py
```

### PASSO 4: Verificar dependências

```bash
# Ativar venv e verificar dependências
cd /var/www/encceja
source venv/bin/activate

# Instalar dependências que podem estar faltando
pip install flask requests qrcode pillow gunicorn python-dotenv

# Verificar instalações
pip list | grep -E "(flask|requests|qrcode|pillow)"
```

### PASSO 5: Corrigir configuração do Supervisor

```bash
# Criar nova configuração do supervisor
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 60 app:app
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/encceja_error.log
stdout_logfile=/var/log/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin",PYTHONPATH="/var/www/encceja"
stopasgroup=true
killasgroup=true
EOF

# Recarregar supervisor
supervisorctl reread
supervisorctl update
supervisorctl stop encceja
supervisorctl start encceja
```

### PASSO 6: Verificar configuração do Nginx

```bash
# Verificar configuração do nginx para o site
cat /etc/nginx/sites-available/encceja

# Se não existir, criar:
cat > /etc/nginx/sites-available/encceja << 'EOF'
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    location /static {
        alias /var/www/encceja/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Habilitar site
ln -sf /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
nginx -t
systemctl reload nginx
```

### PASSO 7: Solução rápida - Arquivo simples de teste

```bash
# Criar arquivo de teste simples
cat > /var/www/encceja/test_app.py << 'EOF'
#!/usr/bin/env python3
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>ENCCEJA 2025 - Teste OK</h1><p>Aplicação funcionando!</p>'

@app.route('/status')
def status():
    return {'status': 'ok', 'message': 'Servidor funcionando'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
EOF

# Testar aplicação simples
cd /var/www/encceja
source venv/bin/activate
python test_app.py
```

### PASSO 8: Configurar supervisor para arquivo de teste

```bash
# Temporariamente usar arquivo de teste
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/test_app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/encceja_error.log
stdout_logfile=/var/log/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin"
EOF

supervisorctl reread
supervisorctl update
supervisorctl start encceja
supervisorctl status encceja
```

### PASSO 9: Verificar funcionamento

```bash
# Testar localmente
curl http://localhost:5000
curl http://localhost:5000/status

# Ver status do supervisor
supervisorctl status encceja

# Se funcionou, acessar via navegador
```

### PASSO 10: Substituir por aplicação principal

```bash
# Depois que o teste funcionar, voltar para app principal
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/encceja_error.log
stdout_logfile=/var/log/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin"
EOF

supervisorctl reread
supervisorctl update
supervisorctl restart encceja
```

## 🔍 COMANDOS DE DIAGNÓSTICO

Execute estes comandos para identificar o problema:

```bash
# 1. Status dos serviços
systemctl status nginx
supervisorctl status

# 2. Processos rodando na porta 5000
netstat -tlnp | grep :5000
lsof -i :5000

# 3. Logs em tempo real
tail -f /var/log/encceja_error.log &
tail -f /var/log/encceja_output.log &
tail -f /var/log/nginx/error.log &

# 4. Testar conexão
curl -v http://localhost:5000
telnet localhost 5000
```

## 🚨 PROBLEMAS MAIS COMUNS

### 1. **Dependências faltando**
Solução: `pip install flask requests qrcode pillow gunicorn`

### 2. **Permissões incorretas**  
Solução: `chown -R www-data:www-data /var/www/encceja`

### 3. **Porta ocupada**
Solução: `pkill -f app.py` ou mudar porta

### 4. **Ambiente virtual corrompido**
Solução: Recriar venv

### 5. **Arquivo app.py com erro de sintaxe**
Solução: Usar arquivo de teste primeiro

## ✅ RESULTADO ESPERADO

Após seguir os passos:
- Supervisor mostra: `encceja: RUNNING`
- Curl local funciona: `curl http://localhost:5000`
- Site carrega sem erro 502
- Logs mostram aplicação iniciada

## 📞 SUPORTE

Se ainda houver problemas, execute:
```bash
# Coletar informações para diagnóstico
echo "=== STATUS SUPERVISOR ==="
supervisorctl status

echo "=== LOGS ERRO ==="
tail -20 /var/log/encceja_error.log

echo "=== PROCESSOS PORTA 5000 ==="
lsof -i :5000

echo "=== TESTE LOCAL ==="
curl -I http://localhost:5000
```