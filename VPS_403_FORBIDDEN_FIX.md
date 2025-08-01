# Correção do Erro 403 Forbidden

## Diagnóstico
O erro 403 indica que a aplicação Python não está rodando e o Nginx não consegue fazer proxy para a porta 5000.

## Comandos de Diagnóstico no VPS:

### 1. Verificar status real da aplicação:
```bash
sudo supervisorctl status
tail -20 /var/log/encceja.log
sudo netstat -tlnp | grep :5000
ps aux | grep gunicorn
```

### 2. Verificar se o domínio está apontando para o VPS:
```bash
curl -I http://IP_DO_VPS
nslookup seu-dominio.com
```

### 3. Verificar configuração do Nginx:
```bash
sudo nginx -t
cat /etc/nginx/sites-enabled/encceja
sudo systemctl status nginx
```

## Soluções:

### Solução 1: Criar aplicação mínima funcional
```bash
cd /var/www/encceja
nano app_simples.py
```

**Conteúdo:**
```python
from flask import Flask
import os

app = Flask(__name__)
app.secret_key = "encceja_secret_2025"

@app.route('/')
def home():
    return '''
    <html>
    <head><title>ENCCEJA 2025</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 100px;">
        <h1>ENCCEJA 2025 - Sistema Online</h1>
        <p>Aplicação Python rodando no VPS com sucesso!</p>
        <p>Servidor funcionando na porta 5000</p>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return "Sistema funcionando perfeitamente!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### Solução 2: Atualizar configuração do Supervisor
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app_simples.py
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
stderr_logfile=/var/log/encceja_error.log
environment=PATH="/var/www/encceja/venv/bin"
```

### Solução 3: Reiniciar serviços
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart encceja
sudo supervisorctl status
```

### Solução 4: Verificar e corrigir Nginx
```bash
sudo nano /etc/nginx/sites-available/encceja
```

**Conteúdo:**
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    error_page 502 503 504 /50x.html;
    location = /50x.html {
        root /var/www/html;
    }
}
```

### Solução 5: Recarregar Nginx
```bash
sudo systemctl reload nginx
sudo systemctl status nginx
```

## Teste Final:
```bash
# Testar aplicação local
curl http://localhost:5000

# Testar via IP externo
curl http://IP_DO_VPS

# Se funcionar, testar o domínio
curl http://seu-dominio.com
```

## Comandos de Emergência:

### Se nada funcionar, rodar aplicação manualmente:
```bash
cd /var/www/encceja
source venv/bin/activate
python app_simples.py
```

### Verificar logs de erro:
```bash
tail -f /var/log/nginx/error.log
tail -f /var/log/encceja.log
```