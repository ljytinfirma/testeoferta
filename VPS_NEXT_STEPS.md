# Próximos Passos - Aplicação Instalada com Sucesso

## Status Atual
✅ Ambiente virtual criado
✅ Dependências instaladas
✅ Pronto para testar a aplicação

## Comandos para Executar Agora:

### 1. Verificar se está no ambiente virtual:
```bash
# Deve mostrar (venv) no prompt
# Se não estiver, ative:
cd /var/www/encceja
source venv/bin/activate
```

### 2. Criar arquivo .env:
```bash
nano .env
```

**Conteúdo do .env:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
```

### 3. Testar aplicação:
```bash
python main.py
```

**Se der erro de arquivo não encontrado:**
```bash
# Verificar arquivos existentes
ls -la

# Se não tiver main.py, criar:
nano main.py
```

**Conteúdo do main.py:**
```python
from app import app
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### 4. Se a aplicação iniciar com sucesso:
```bash
# Deve mostrar algo como:
# * Running on all addresses (0.0.0.0)
# * Running on http://127.0.0.1:5000
# * Running on http://[IP_DO_VPS]:5000

# Pressionar Ctrl+C para parar e continuar configuração
```

### 5. Configurar Supervisor:
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PATH="/var/www/encceja/venv/bin"
```

### 6. Ativar Supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start encceja
sudo supervisorctl status
```

### 7. Verificar se está rodando:
```bash
# Verificar logs
tail -f /var/log/encceja.log

# Testar acesso local
curl http://localhost:5000
```

### 8. Configurar Nginx (opcional mas recomendado):
```bash
sudo nano /etc/nginx/sites-available/encceja
```

**Conteúdo:**
```nginx
server {
    listen 80;
    server_name SEU_DOMINIO.com www.SEU_DOMINIO.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /var/www/encceja/static;
        expires 30d;
    }
}
```

### 9. Ativar site no Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 10. Testar acesso externo:
```bash
# Acessar via IP do VPS
curl http://IP_DO_SEU_VPS

# Ou pelo domínio (se configurado)
curl http://seu-dominio.com
```

## Comandos de Diagnóstico

### Se algo não funcionar:
```bash
# Ver logs da aplicação
tail -f /var/log/encceja.log

# Status do supervisor
sudo supervisorctl status

# Status do nginx
sudo systemctl status nginx

# Verificar se a porta 5000 está em uso
sudo netstat -tlnp | grep :5000

# Verificar processos Python
ps aux | grep python
```

## Estrutura Final Esperada

```
/var/www/encceja/
├── venv/                    # Ambiente virtual Python
├── main.py                  # Ponto de entrada
├── app.py                   # Aplicação Flask
├── .env                     # Variáveis de ambiente
├── requirements.txt         # Dependências (opcional)
├── templates/              # Templates HTML
├── static/                 # CSS, JS, imagens
└── witepay_gateway.py      # Gateway de pagamento
```

Siga estes passos e sua aplicação estará rodando no VPS!