# Correção do Erro "ModuleNotFoundError: No module named 'dotenv'"

## Problema Identificado
O erro mostra que o módulo `python-dotenv` não está instalado no ambiente Python do VPS.

## Solução Passo a Passo

### 1. Conectar no VPS via SSH
```bash
# No MobaXterm, conecte no VPS
ssh root@SEU_IP_VPS
```

### 2. Navegar para o Diretório do Projeto
```bash
cd /var/www/encceja
```

### 3. Ativar Ambiente Virtual (se criado)
```bash
# Se você criou um ambiente virtual
source venv/bin/activate

# Verificar se está ativo (deve aparecer (venv) no prompt)
```

### 4. Instalar Dependências em Falta
```bash
# Instalar python-dotenv especificamente
pip3 install python-dotenv

# Instalar todas as dependências do projeto
pip3 install flask gunicorn python-dotenv requests qrcode pillow psycopg2-binary twilio email-validator flask-sqlalchemy
```

### 5. Verificar Instalação
```bash
python3 -c "import dotenv; print('dotenv instalado com sucesso!')"
```

### 6. Criar Arquivo requirements.txt (se não existir)
```bash
nano requirements.txt
```

**Conteúdo do requirements.txt:**
```txt
Flask==2.3.3
gunicorn==21.2.0
python-dotenv==1.0.0
requests==2.31.0
qrcode==7.4.2
Pillow==10.0.1
psycopg2-binary==2.9.7
twilio==8.10.0
email-validator==2.1.0
Flask-SQLAlchemy==3.1.1
```

### 7. Instalar a partir do requirements.txt
```bash
pip3 install -r requirements.txt
```

### 8. Configurar Variáveis de Ambiente
```bash
nano .env
```

**Conteúdo do .env:**
```env
SESSION_SECRET=sua_chave_secreta_super_segura_123456789
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
```

### 9. Testar a Aplicação Manualmente
```bash
# Testar se a aplicação inicia
python3 main.py
```

### 10. Se ainda der erro, verificar o main.py
```bash
nano main.py
```

**Conteúdo correto do main.py:**
```python
from app import app
import os

if __name__ == "__main__":
    # Para produção no VPS
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### 11. Configurar Gunicorn
```bash
# Testar com Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
```

### 12. Configurar Supervisor para Executar Automaticamente
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo:**
```ini
[program:encceja]
command=/usr/bin/python3 -m gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PATH="/usr/bin"
```

### 13. Recarregar Supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start encceja
sudo supervisorctl status
```

### 14. Verificar Logs
```bash
# Ver logs da aplicação
tail -f /var/log/encceja.log

# Ver status do supervisor
sudo supervisorctl status encceja
```

## Comandos de Diagnóstico

### Se ainda houver problemas:
```bash
# Verificar versão do Python
python3 --version

# Verificar módulos instalados
pip3 list

# Verificar se o arquivo main.py existe
ls -la main.py

# Verificar se o arquivo app.py existe
ls -la app.py

# Testar importação
python3 -c "from app import app; print('App importado com sucesso!')"
```

## Estrutura de Arquivos Esperada

```
/var/www/encceja/
├── main.py              # Ponto de entrada
├── app.py               # Aplicação Flask principal
├── requirements.txt     # Dependências Python
├── .env                # Variáveis de ambiente
├── templates/          # Templates HTML
├── static/            # CSS, JS, imagens
└── witepay_gateway.py # Gateway de pagamento
```

## Permissões de Arquivo

```bash
# Ajustar permissões se necessário
sudo chown -R root:root /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 644 /var/www/encceja/*.py
```

## Teste Final

```bash
# Testar aplicação localmente no VPS
curl http://localhost:5000

# Se retornar HTML, está funcionando
# Agora configure o Nginx para servir na porta 80
```

## Se Continuar com Problemas

### Reinstalar Python e dependências:
```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Reinstalar Python
sudo apt install python3 python3-pip python3-venv -y

# Criar novo ambiente virtual
python3 -m venv /var/www/encceja/venv
source /var/www/encceja/venv/bin/activate

# Instalar dependências no ambiente virtual
pip install -r requirements.txt
```

### Usar o ambiente virtual no supervisor:
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
```

Siga estes passos e a aplicação deve funcionar corretamente no VPS!