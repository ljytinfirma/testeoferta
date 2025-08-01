# Verificação do Status da Aplicação

## Comandos para Verificar se Está Funcionando:

### 1. Verificar status do supervisor:
```bash
sudo supervisorctl status
```

### 2. Verificar logs da aplicação:
```bash
tail -f /var/log/encceja.log
```

### 3. Testar se a aplicação responde:
```bash
curl http://localhost:5000
```

### 4. Verificar se a porta 5000 está ativa:
```bash
sudo netstat -tlnp | grep :5000
```

### 5. Ver processos Python rodando:
```bash
ps aux | grep python
```

## Se Estiver Funcionando:

### Configurar Nginx para servir na porta 80:
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
    }

    location /static {
        alias /var/www/encceja/static;
        expires 30d;
    }
}
```

### Ativar o site:
```bash
sudo ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Testar acesso externo:
```bash
curl http://IP_DO_SEU_VPS
```

## Comandos de Resolução de Problemas:

### Se não estiver funcionando:
```bash
# Parar e reiniciar
sudo supervisorctl stop encceja
sudo supervisorctl start encceja

# Ver erros detalhados
tail -50 /var/log/encceja.log

# Testar manualmente
cd /var/www/encceja
source venv/bin/activate
python main.py
```