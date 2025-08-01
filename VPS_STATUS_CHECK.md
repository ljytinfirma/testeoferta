# Status Check e Correção do VPS

## Situação Atual
✅ Aplicação Python rodando no Replit
✅ Logs mostram: "Renderizando página inicial"
❌ Domínio mostra 403 Forbidden
🎯 Problema: Configuração VPS/Nginx

## Comandos de Diagnóstico no VPS:

### 1. Verificar se aplicação está rodando na porta 5000:
```bash
sudo supervisorctl status
sudo netstat -tlnp | grep :5000
curl http://localhost:5000
```

### 2. Verificar configuração do Nginx:
```bash
sudo nginx -t
cat /etc/nginx/sites-enabled/encceja
sudo systemctl status nginx
```

### 3. Verificar logs de erro:
```bash
tail -20 /var/log/nginx/error.log
tail -20 /var/log/nginx/access.log
```

### 4. Verificar se o domínio aponta para o VPS:
```bash
nslookup seu-dominio.com
curl -I http://IP_DO_VPS
```

## Possíveis Soluções:

### Solução 1: Recriar configuração do Nginx
```bash
sudo rm /etc/nginx/sites-enabled/encceja
sudo nano /etc/nginx/sites-available/encceja
```

**Conteúdo correto:**
```nginx
server {
    listen 80;
    server_name _ seu-dominio.com www.seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }

    access_log /var/log/nginx/encceja_access.log;
    error_log /var/log/nginx/encceja_error.log;
}
```

```bash
sudo ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### Solução 2: Remover configuração padrão conflitante
```bash
sudo rm /etc/nginx/sites-enabled/default
sudo systemctl reload nginx
```

### Solução 3: Verificar firewall
```bash
sudo ufw status
sudo ufw allow 80
sudo ufw allow 443
```

### Solução 4: Testar aplicação Python diretamente
```bash
cd /var/www/encceja
source venv/bin/activate
python main.py
# Testar em outro terminal: curl http://localhost:5000
```

### Solução 5: Reiniciar todos os serviços
```bash
sudo supervisorctl restart encceja
sudo systemctl restart nginx
sudo systemctl status nginx
sudo supervisorctl status
```

## Teste de Conectividade:

### No VPS, testar:
```bash
# 1. Aplicação local
curl -v http://localhost:5000

# 2. Via IP externo  
curl -v http://IP_DO_VPS

# 3. Verificar porta 80
sudo netstat -tlnp | grep :80
```

### Se IP funcionar mas domínio não:
- Problema está no DNS
- Verificar se domínio aponta para IP correto
- Aguardar propagação DNS (até 24h)

## Logs para Monitorar:
```bash
# Terminal 1: Logs da aplicação
tail -f /var/log/encceja.log

# Terminal 2: Logs do Nginx
tail -f /var/log/nginx/error.log

# Terminal 3: Logs de acesso
tail -f /var/log/nginx/access.log
```

## Comandos de Emergência:

### Se nada funcionar:
```bash
# Parar nginx temporariamente
sudo systemctl stop nginx

# Rodar aplicação na porta 80 diretamente
cd /var/www/encceja
source venv/bin/activate
sudo /var/www/encceja/venv/bin/python main.py --port 80
```

## Estrutura de Arquivos que Deve Existir:
```
/var/www/encceja/
├── venv/                    # ✅ Existe
├── app.py                   # ❓ Verificar se é o real
├── main.py                  # ❓ Verificar se é o real  
├── templates/               # ❓ Deve ter todos os HTMLs
│   ├── index.html
│   ├── encceja_info.html
│   └── pagamento.html
└── static/                  # ❓ CSS e fontes
    └── css/output.css
```

Execute estes comandos na ordem e me informe os resultados!