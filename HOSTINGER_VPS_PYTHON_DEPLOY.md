# Deploy Python Flask no VPS Hostinger via MobaXterm

## Pré-requisitos
- VPS Hostinger contratado
- MobaXterm instalado
- Dados de acesso SSH do VPS
- Projeto Python/Flask pronto

## Passo 1: Obter Dados de Acesso SSH

### Via hPanel Hostinger:
1. Login no hPanel → **VPS** → **Gerenciar**
2. Procure por **Acesso SSH** ou **Detalhes do Servidor**
3. Anote:
   ```
   IP: 123.45.67.89 (IP do seu VPS)
   Usuário: root (ou usuário criado)
   Senha: sua_senha_vps
   Porta: 22
   ```

## Passo 2: Conectar via MobaXterm

### Configurar Sessão SSH:
1. **MobaXterm** → **Session** → **New Session**
2. Escolha **SSH**
3. Configure:
   ```
   Remote host: 123.45.67.89 (IP do VPS)
   Username: root
   Port: 22
   ```
4. **OK** → Digite a senha quando solicitado

## Passo 3: Preparar o Servidor

### Atualizar sistema e instalar Python:
```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar Python e ferramentas
sudo apt install python3 python3-pip python3-venv nginx git -y

# Verificar instalação
python3 --version
pip3 --version
```

### Instalar supervisor (gerenciar processos):
```bash
sudo apt install supervisor -y
```

## Passo 4: Upload do Projeto

### Método 1 - Via MobaXterm (Upload Direto):
1. **Painel esquerdo** (local) → Navegue até sua pasta do projeto
2. **Painel direito** (servidor) → Vá para `/var/www/`
3. **Drag & Drop** todos os arquivos do projeto:
   ```
   /var/www/encceja/
   ├── app.py
   ├── main.py
   ├── requirements.txt
   ├── templates/
   ├── static/
   └── witepay_gateway.py
   ```

### Método 2 - Via Git (se estiver no GitHub):
```bash
cd /var/www/
git clone https://github.com/seu-usuario/seu-projeto.git encceja
cd encceja
```

## Passo 5: Configurar Ambiente Python

### Criar ambiente virtual:
```bash
cd /var/www/encceja
python3 -m venv venv
source venv/bin/activate
```

### Instalar dependências:
```bash
pip install -r requirements.txt

# Se não tiver requirements.txt, instalar manualmente:
pip install flask gunicorn python-dotenv requests qrcode psycopg2-binary twilio email-validator flask-sqlalchemy
```

## Passo 6: Configurar Variáveis de Ambiente

### Criar arquivo .env:
```bash
nano .env
```

### Adicionar variáveis:
```env
SESSION_SECRET=sua_chave_secreta_aqui
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DATABASE_URL=postgresql://user:password@localhost/dbname
DOMAIN_RESTRICTION_ENABLED=true
```

## Passo 7: Configurar Gunicorn

### Criar arquivo de configuração:
```bash
nano gunicorn.conf.py
```

### Conteúdo do arquivo:
```python
bind = "0.0.0.0:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
reload = False
```

### Testar aplicação:
```bash
source venv/bin/activate
gunicorn --config gunicorn.conf.py main:app
```

## Passo 8: Configurar Supervisor

### Criar arquivo de configuração:
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

### Conteúdo:
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --config /var/www/encceja/gunicorn.conf.py main:app
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
```

### Ativar supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start encceja
sudo supervisorctl status
```

## Passo 9: Configurar Nginx

### Criar configuração do site:
```bash
sudo nano /etc/nginx/sites-available/encceja
```

### Conteúdo:
```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;

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

### Ativar site:
```bash
sudo ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Passo 10: Configurar Domínio

### No painel da Hostinger:
1. **Domínios** → **Gerenciar DNS**
2. Adicionar/editar registro **A**:
   ```
   Nome: @ (ou www)
   Tipo: A
   Valor: 123.45.67.89 (IP do VPS)
   TTL: 3600
   ```

## Passo 11: SSL (Opcional mas Recomendado)

### Instalar Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com
```

## Passo 12: Testar Aplicação

### Verificar status:
```bash
# Status do supervisor
sudo supervisorctl status encceja

# Status do nginx
sudo systemctl status nginx

# Logs da aplicação
tail -f /var/log/encceja.log
```

### Acessar site:
- **HTTP**: `http://seu-dominio.com`
- **HTTPS**: `https://seu-dominio.com` (se SSL configurado)

## Comandos Úteis para Manutenção

### Reiniciar aplicação:
```bash
sudo supervisorctl restart encceja
```

### Ver logs:
```bash
tail -f /var/log/encceja.log
```

### Atualizar código:
```bash
cd /var/www/encceja
git pull origin main  # se usando Git
sudo supervisorctl restart encceja
```

## Estrutura Final no VPS

```
/var/www/encceja/
├── venv/                    # Ambiente virtual Python
├── app.py                   # Aplicação Flask
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências
├── .env                     # Variáveis de ambiente
├── gunicorn.conf.py        # Configuração Gunicorn
├── templates/              # Templates HTML
├── static/                 # CSS, JS, imagens
└── witepay_gateway.py      # Gateway de pagamento
```

## Solução de Problemas

### Aplicação não inicia:
```bash
# Verificar logs
sudo supervisorctl tail -f encceja

# Testar manualmente
cd /var/www/encceja
source venv/bin/activate
python3 main.py
```

### Erro 502 Bad Gateway:
```bash
# Verificar se Gunicorn está rodando
sudo supervisorctl status encceja

# Verificar configuração Nginx
sudo nginx -t
```

### Erro de permissões:
```bash
sudo chown -R www-data:www-data /var/www/encceja
sudo chmod -R 755 /var/www/encceja
```

## Custos Estimados

- **VPS Básico Hostinger**: R$ 15-25/mês
- **Domínio**: R$ 40/ano (se não tiver)
- **SSL**: Grátis (Let's Encrypt)

## Conclusão

Após seguir estes passos, seu projeto Python Flask estará rodando no VPS da Hostinger com:
- ✅ Python/Flask funcionando
- ✅ Nginx como proxy reverso
- ✅ Supervisor gerenciando processos
- ✅ SSL configurado
- ✅ Domínio apontando corretamente
- ✅ WitePay PIX funcionais
- ✅ Funil ENCCEJA completo