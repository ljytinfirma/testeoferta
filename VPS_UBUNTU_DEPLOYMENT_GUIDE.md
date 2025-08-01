# Guia de Deploy - Ubuntu VPS Hostinger
## Sistema ENCCEJA com WitePay PIX

### Pré-requisitos
- VPS Ubuntu na Hostinger
- Acesso SSH ao servidor
- Domínio configurado (opcional)

## 1. Conectar ao VPS via SSH

```bash
ssh root@SEU_IP_VPS
# Ou use o terminal web da Hostinger
```

## 2. Atualizar Sistema

```bash
apt update && apt upgrade -y
```

## 3. Instalar Dependências

```bash
# Python 3.11 e pip
apt install python3.11 python3.11-pip python3.11-venv -y

# Nginx (servidor web)
apt install nginx -y

# Supervisor (gerenciador de processos)
apt install supervisor -y

# Git para clonar projetos
apt install git -y

# Certbot para SSL (opcional)
apt install certbot python3-certbot-nginx -y
```

## 4. Criar Diretório do Projeto

```bash
mkdir -p /var/www/encceja
cd /var/www/encceja
```

## 5. Fazer Upload dos Arquivos

### Opção A: Via SCP (do seu computador local)
```bash
scp -r ./projeto-encceja/* root@SEU_IP:/var/www/encceja/
```

### Opção B: Criar arquivos manualmente
```bash
# Copie todos os arquivos do projeto para /var/www/encceja/
# Incluindo: app.py, templates/, static/, requirements.txt
```

## 6. Configurar Ambiente Python

```bash
cd /var/www/encceja

# Criar ambiente virtual
python3.11 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

## 7. Configurar Variáveis de Ambiente

```bash
# Criar arquivo .env
cat > .env << EOF
SESSION_SECRET=sua_chave_secreta_super_forte_aqui_$(openssl rand -hex 32)
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
CPF_API_TOKEN=1285fe4s-e931-4071-a848-3fac8273c55a
FLASK_ENV=production
EOF

# Definir permissões
chmod 600 .env
chown www-data:www-data .env
```

## 8. Configurar Gunicorn

```bash
# Criar arquivo de configuração do Gunicorn
cat > gunicorn.conf.py << EOF
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
EOF
```

## 9. Configurar Supervisor

```bash
# Criar configuração do Supervisor
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

# Recarregar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start encceja
```

## 10. Configurar Nginx

```bash
# Criar configuração do Nginx
cat > /etc/nginx/sites-available/encceja << EOF
server {
    listen 80;
    server_name SEU_DOMINIO.COM SEU_IP_VPS;
    
    client_max_body_size 10M;
    
    location /static/ {
        alias /var/www/encceja/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

# Ativar site
ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reiniciar Nginx
systemctl restart nginx
systemctl enable nginx
```

## 11. Configurar Firewall

```bash
# Abrir portas necessárias
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 12. Configurar SSL (Opcional - Recomendado)

```bash
# Apenas se você tiver um domínio configurado
certbot --nginx -d SEU_DOMINIO.COM
```

## 13. Verificar Status dos Serviços

```bash
# Verificar status do supervisor
supervisorctl status encceja

# Verificar logs
tail -f /var/log/encceja.log

# Verificar Nginx
systemctl status nginx

# Testar aplicação
curl -I http://localhost:5000
```

## 14. Comandos Úteis para Manutenção

```bash
# Reiniciar aplicação
supervisorctl restart encceja

# Ver logs em tempo real
tail -f /var/log/encceja.log

# Atualizar código (após fazer upload de novos arquivos)
cd /var/www/encceja
source venv/bin/activate
pip install -r requirements.txt --upgrade
supervisorctl restart encceja

# Backup do projeto
tar -czf /backup/encceja-$(date +%Y%m%d).tar.gz /var/www/encceja
```

## 15. Solução de Problemas Comuns

### App não inicia
```bash
# Verificar logs
tail -n 50 /var/log/encceja.log

# Verificar se porta está em uso
netstat -tlnp | grep :5000
```

### Erro de permissões
```bash
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
```

### Nginx 502 Bad Gateway
```bash
# Verificar se Gunicorn está rodando
supervisorctl status encceja

# Reiniciar serviços
supervisorctl restart encceja
systemctl restart nginx
```

## Estrutura Final do Projeto

```
/var/www/encceja/
├── app.py
├── requirements.txt
├── gunicorn.conf.py
├── .env
├── venv/
├── templates/
│   ├── inscricao.html
│   ├── pagamento.html
│   ├── validar_dados.html
│   ├── endereco.html
│   ├── local_prova.html
│   ├── encceja_info.html
│   └── inscricao_sucesso.html
└── static/
    ├── css/
    ├── js/
    ├── images/
    └── fonts/
```

## Acesso ao Sistema

Após o deploy, o sistema estará disponível em:
- HTTP: `http://SEU_IP_VPS` ou `http://SEU_DOMINIO.COM`
- HTTPS: `https://SEU_DOMINIO.COM` (se SSL configurado)

O sistema funcionará com:
- ✅ Consulta CPF via API real
- ✅ Geração de PIX WitePay
- ✅ QR Code funcional
- ✅ Valor R$ 93,40
- ✅ Todos os templates funcionando