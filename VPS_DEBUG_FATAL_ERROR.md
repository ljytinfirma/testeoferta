# Diagnóstico: Erro FATAL no Supervisor

## Comandos para Diagnosticar o Problema:

### 1. Ver logs detalhados da aplicação:
```bash
tail -50 /var/log/encceja.log
```

### 2. Ver logs do supervisor:
```bash
sudo tail -50 /var/log/supervisor/supervisord.log
```

### 3. Verificar se os arquivos existem:
```bash
ls -la /var/www/encceja/
ls -la /var/www/encceja/main.py
ls -la /var/www/encceja/app.py
```

### 4. Testar aplicação manualmente:
```bash
cd /var/www/encceja
source venv/bin/activate
python main.py
```

## Possíveis Causas e Soluções:

### Causa 1: Arquivo main.py não existe
```bash
# Criar main.py
nano /var/www/encceja/main.py
```

**Conteúdo:**
```python
from app import app
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### Causa 2: Arquivo app.py não existe ou está incompleto
```bash
# Verificar conteúdo do app.py
cat /var/www/encceja/app.py
```

### Causa 3: Problema na configuração do supervisor
```bash
# Verificar configuração
cat /etc/supervisor/conf.d/encceja.conf

# Recriar configuração
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Configuração correta:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
stderr_logfile=/var/log/encceja_error.log
environment=PATH="/var/www/encceja/venv/bin"
```

### Causa 4: Problema de permissões
```bash
sudo chown -R root:root /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 644 /var/www/encceja/*.py
```

### Depois de corrigir, reiniciar supervisor:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl restart encceja
sudo supervisorctl status
```

## Teste Alternativo com Gunicorn Direto:

### Se supervisor continuar falhando:
```bash
cd /var/www/encceja
source venv/bin/activate
/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

## Criação de Arquivos Básicos:

### Se main.py não existir:
```python
# /var/www/encceja/main.py
from app import app
import os

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### Se app.py não existir (versão mínima):
```python
# /var/www/encceja/app.py
from flask import Flask, render_template, request, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret_key")

@app.route('/')
def index():
    return "<h1>ENCCEJA 2025 - Sistema Online</h1><p>Aplicação rodando com sucesso no VPS!</p>"

@app.route('/test')
def test():
    return "Sistema funcionando!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```