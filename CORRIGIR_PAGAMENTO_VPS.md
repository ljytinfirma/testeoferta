# 🔧 CORREÇÃO ESPECÍFICA: Erro 403 WitePay na VPS

## 🎯 Problema Identificado

**Erro:** "Erro ao criar ordem 403"  
**Causa:** A chave da API WitePay na VPS está incorreta ou não tem permissões suficientes.

---

## ✅ Solução Imediata

### 1️⃣ Verificar chave API na VPS
```bash
# Conectar na VPS
ssh root@SEU_IP_VPS

# Verificar se a variável existe
echo $WITEPAY_API_KEY

# Se vazia, verificar no arquivo .env
cat /var/www/encceja/.env | grep WITEPAY
```

### 2️⃣ Configurar chave correta
```bash
# Editar arquivo .env na VPS
nano /var/www/encceja/.env

# Adicionar/corrigir linha:
WITEPAY_API_KEY=SUA_CHAVE_WITEPAY_REAL_AQUI
```

### 3️⃣ Testar chave API diretamente na VPS
```bash
# Testar criação de ordem
curl -X POST "https://api.witepay.com.br/v1/order/create" \
  -H "x-api-key: SUA_CHAVE_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "productData": [
      {
        "name": "Teste ENCCEJA",
        "value": 9340
      }
    ],
    "clientData": {
      "clientName": "Teste",
      "clientDocument": "11111111000111",
      "clientEmail": "teste@gmail.com",
      "clientPhone": "11987790088"
    }
  }'
```

**Resultado esperado:**
```json
{"status":"success","orderId":"or_xxxxx"}
```

### 4️⃣ Reiniciar aplicação
```bash
# Reiniciar para carregar nova chave
sudo supervisorctl restart encceja

# Verificar logs
tail -f /var/log/supervisor/encceja.log | grep "\[VPS\]"
```

---

## 🔍 Diagnóstico Completo

### Como obter chave WitePay correta:

1. **Acessar painel WitePay**
2. **Ir em Configurações → API Keys**
3. **Copiar chave de PRODUÇÃO** (não sandbox)
4. **Verificar permissões** (deve ter acesso a orders e charges)

### Formato da chave WitePay:
```
WITEPAY_API_KEY=wtp_sk_xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🧪 Teste Final

Após configurar a chave correta:

```bash
# 1. Testar criação de pagamento
curl -X POST "http://localhost:5000/criar-pagamento-pix" \
  -H "Content-Type: application/json" \
  -d '{}'

# 2. Resultado esperado:
{
  "success": true,
  "id": "ch_xxxxx",
  "pixCode": "00020101021226840014br.gov.bcb.pix...",
  "amount": 93.40
}
```

---

## ⚠️ Pontos Importantes

1. **Chave diferente por ambiente:**
   - Replit usa uma chave de teste
   - VPS precisa da chave de produção real

2. **Permissões necessárias:**
   - Criar orders (`/v1/order/create`)
   - Criar charges (`/v1/charge/create`)
   - Consultar status (`/v1/charge/{id}`)

3. **Formato de dados específico:**
   - `paymentMethod`: "pix" (minúsculas)
   - `value`: em centavos (9340 = R$ 93,40)
   - `clientDocument`: só números

---

## 📞 Se Ainda Não Funcionar

### Verificar logs detalhados:
```bash
grep -A 5 -B 5 "403" /var/log/supervisor/encceja.log
```

### Contatar suporte WitePay:
- Verificar se conta está ativa
- Confirmar limites da API
- Solicitar chave com permissões completas

---

## 🎯 Status Final

Após seguir estes passos:
- ✅ Chave API configurada corretamente
- ✅ Teste de ordem retorna success
- ✅ Página de pagamento gera PIX instantaneamente
- ✅ Valor R$ 93,40 correto
- ✅ QR Code válido gerado

**A configuração correta da chave WitePay resolve definitivamente o erro 403!**