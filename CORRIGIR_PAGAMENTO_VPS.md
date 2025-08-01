# 🔧 Correção Pagamento PIX - VPS

## ❌ Problema Identificado
O sistema de pagamento WitePay estava com erro na geração do PIX devido a problemas na implementação do gateway e conflitos entre diferentes versões do código.

## ✅ Solução Implementada
Criado sistema de pagamento PIX simplificado e funcional especificamente para VPS.

---

## 🚀 Arquivos Corrigidos para VPS

### 1. Gateway WitePay Corrigido
**`VPS_WITEPAY_CORRIGIDO.py`** → Renomear para `witepay_gateway.py`

### 2. App Principal Corrigido  
**`VPS_APP_PAGAMENTO_CORRIGIDO.py`** → Renomear para `app.py`

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

### 3️⃣ Fazer backup dos arquivos atuais
```bash
cp app.py app_backup_pagamento_$(date +%Y%m%d_%H%M%S).py
cp witepay_gateway.py witepay_backup_$(date +%Y%m%d_%H%M%S).py
```

### 4️⃣ Upload dos arquivos corrigidos
**No MobaXterm (painel lateral):**
1. Arraste `VPS_WITEPAY_CORRIGIDO.py` para `/var/www/encceja`
2. Arraste `VPS_APP_PAGAMENTO_CORRIGIDO.py` para `/var/www/encceja`

### 5️⃣ Renomear arquivos
```bash
mv VPS_WITEPAY_CORRIGIDO.py witepay_gateway.py
mv VPS_APP_PAGAMENTO_CORRIGIDO.py app.py
```

### 6️⃣ Verificar sintaxe
```bash
python -c "import app; print('App OK')"
python -c "import witepay_gateway; print('Gateway OK')"
```

### 7️⃣ Testar localmente
```bash
python main.py
```

**Saída esperada:**
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

### 8️⃣ Testar rota de pagamento
```bash
# Em outro terminal SSH
curl -X POST "http://localhost:5000/criar-pagamento-pix" \
  -H "Content-Type: application/json" \
  -d '{}' | head -10
```

**Resultado esperado:** JSON com dados do PIX (não erro 500)

### 9️⃣ Parar teste e reiniciar produção
```bash
# Pressionar Ctrl+C para parar teste
sudo supervisorctl restart encceja
sudo systemctl reload nginx
```

### 🔟 Verificar status
```bash
sudo supervisorctl status
```

**Saída esperada:**
```
encceja    RUNNING   pid 1234, uptime 0:00:05
```

---

## 🎯 Diferenças da Correção

### ❌ Problema Original
- Conflito entre múltiplas implementações do WitePay
- Função `create_witepay_gateway()` não existia
- Estrutura de dados inconsistente
- Timeout e erros de conexão

### ✅ Versão Corrigida
- **Gateway simplificado** com funções diretas
- **Dados padronizados** para ENCCEJA (R$ 93,40)
- **Tratamento de erros** completo
- **Logging detalhado** para debug
- **Timeouts configurados** para evitar travamentos

---

## 🧪 Teste Completo do Pagamento

### 1. Acesse a página de pagamento
**URL:** `http://seu-dominio.com/pagamento`

### 2. Abra o Console do navegador (F12)

### 3. Execute o teste:
```javascript
// Simular clique no botão de pagamento
document.querySelector('.payment-button').click();
```

### 4. Resultados esperados:
- ✅ **Não aparece erro 500**
- ✅ **Código PIX é gerado**
- ✅ **QR Code aparece**
- ✅ **Valor exibido: R$ 93,40**

---

## 🔍 Verificação de Logs

Se ainda houver problemas:

```bash
# Ver logs da aplicação em tempo real
tail -f /var/log/supervisor/encceja.log

# Ver logs específicos do WitePay
grep -i "witepay\|pagamento\|pix" /var/log/supervisor/encceja.log | tail -20

# Testar conexão com API WitePay
curl -X POST "https://api.witepay.com.br/v1/order/create" \
  -H "x-api-key: SUA_CHAVE_AQUI" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

---

## 🔐 Variáveis de Ambiente Necessárias

Certifique-se que o arquivo `.env` contém:

```bash
WITEPAY_API_KEY=sua_chave_witepay_aqui
SESSION_SECRET=encceja_secret_2025
```

---

## ✅ Checklist de Validação

- [ ] Backup dos arquivos originais realizado
- [ ] Arquivos corrigidos enviados e renomeados
- [ ] Sintaxe verificada (import sem erro)
- [ ] Teste local funcionando
- [ ] Supervisor reiniciado
- [ ] Nginx recarregado
- [ ] Página de pagamento carrega sem erro
- [ ] Botão "Gerar PIX" funciona
- [ ] Código PIX é exibido
- [ ] QR Code é gerado
- [ ] Valor correto (R$ 93,40)
- [ ] Logs não mostram erro 500

---

## 🎯 Resultado Final

Após esta correção:

✅ **Pagamento PIX funcionando** - Fim dos erros 500  
✅ **Gateway WitePay estável** - Conexão correta com API  
✅ **Código PIX gerado** - Transação válida de R$ 93,40  
✅ **QR Code exibido** - Pagamento via celular funcionando  
✅ **Logs detalhados** - Debug facilitado para problemas futuros  

**O sistema de pagamento ENCCEJA estará 100% funcional no VPS!**

---

## 📞 Em Caso de Problemas

Se o pagamento ainda não funcionar:

1. **Verifique a chave da API:**
   ```bash
   echo $WITEPAY_API_KEY
   ```

2. **Teste conectividade:**
   ```bash
   curl -I https://api.witepay.com.br/v1/
   ```

3. **Veja logs em tempo real:**
   ```bash
   tail -f /var/log/supervisor/encceja.log
   ```

Com esta correção, o erro do pagamento será resolvido!