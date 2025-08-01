# Solução: Ambiente Python "Externally Managed" no VPS

## Problema
O sistema Ubuntu/Debian está protegendo o Python global com "externally-managed-environment".

## Solução: Usar Ambiente Virtual

### Comandos para Executar no Terminal VPS:

```bash
# 1. Navegar para o diretório do projeto
cd /var/www/encceja

# 2. Criar ambiente virtual
python3 -m venv venv

# 3. Ativar ambiente virtual
source venv/bin/activate

# 4. Agora instalar as dependências (dentro do venv)
pip install python-dotenv flask gunicorn requests qrcode pillow psycopg2-binary twilio email-validator flask-sqlalchemy

# 5. Verificar se instalou corretamente
pip list

# 6. Testar aplicação
python main.py
```

### Se der erro no psycopg2-binary:

```bash
# Instalar dependências do sistema primeiro
sudo apt update
sudo apt install libpq-dev python3-dev build-essential -y

# Depois instalar novamente
pip install psycopg2-binary
```

### Configurar Supervisor com Ambiente Virtual:

```bash
# Editar configuração do supervisor
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo com caminho correto do venv:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PATH="/var/www/encceja/venv/bin:%(ENV_PATH)s"
```

### Recarregar supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start encceja
sudo supervisorctl status
```

### Verificar logs:
```bash
tail -f /var/log/encceja.log
```