# 🔧 CORREÇÃO: QR Code PIX Vazio na VPS

## 🎯 Problema Atual

**Status:** API WitePay funcionando (não mais erro 403)  
**Novo erro:** "Código PIX não encontrado"  
**Causa:** A resposta da API não contém o campo `qrCode` ou está vazio

---

## ✅ Solução Aplicada

### Correções implementadas no VPS_DEFINITIVO_APP.py:

1. **Múltiplos campos de QR Code:**
   ```python
   pix_code = charge_result.get('qrCode') or charge_result.get('pixCode') or charge_result.get('pix_code')
   ```

2. **Tentativa dupla de obtenção:**
   - Primeira tentativa na criação da cobrança
   - Segunda tentativa após 2 segundos (caso precise processar)

3. **Logs detalhados:**
   - Log completo da resposta da API
   - Debug info em caso de erro

4. **Fallback robusto:**
   - Consulta status da cobrança se QR code vazio
   - Múltiplos campos de ID de transação

---

## 🧪 Teste na VPS

### 1. Aplicar a correção:
```bash
# Na VPS, substituir o arquivo
mv VPS_DEFINITIVO_APP.py app.py
sudo supervisorctl restart encceja
```

### 2. Testar criação de pagamento:
```bash
curl -X POST "http://localhost:5000/criar-pagamento-pix" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### 3. Verificar logs detalhados:
```bash
tail -f /var/log/supervisor/encceja.log | grep -A 10 "\[VPS\] Dados da cobrança"
```

---

## 🔍 Diagnóstico de Problemas

### Se ainda der erro de QR code:

1. **Verificar resposta completa da API:**
   ```bash
   grep "Dados da cobrança recebidos" /var/log/supervisor/encceja.log | tail -1
   ```

2. **Testar API diretamente:**
   ```bash
   # Criar ordem
   ORDER_ID=$(curl -s -X POST "https://api.witepay.com.br/v1/order/create" \
     -H "x-api-key: $WITEPAY_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"productData":[{"name":"Teste","value":9340}],"clientData":{"clientName":"Teste","clientDocument":"11111111000111","clientEmail":"teste@gmail.com","clientPhone":"11987790088"}}' \
     | grep -o '"orderId":"[^"]*"' | cut -d'"' -f4)
   
   # Criar cobrança
   curl -s -X POST "https://api.witepay.com.br/v1/charge/create" \
     -H "x-api-key: $WITEPAY_API_KEY" \
     -H "Content-Type: application/json" \
     -d "{\"paymentMethod\":\"pix\",\"orderId\":\"$ORDER_ID\"}"
   ```

3. **Verificar configuração da conta WitePay:**
   - Conta ativada para PIX
   - Limites de transação configurados
   - Webhooks configurados (se necessário)

---

## 🎯 Possíveis Causas do QR Code Vazio

1. **Conta WitePay em sandbox:** Verificar se está usando produção
2. **Configuração PIX pendente:** Conta pode precisar ativar PIX
3. **Processamento assíncrono:** API pode demorar para gerar QR
4. **Limites de valor:** R$ 93,40 pode estar fora dos limites configurados

---

## 📞 Próximos Passos

### Se a correção funcionar:
- ✅ QR Code aparece na página
- ✅ Valor R$ 93,40 correto
- ✅ Código PIX com 200+ caracteres

### Se ainda não funcionar:
1. **Contatar suporte WitePay** para verificar:
   - Status da conta
   - Configuração PIX
   - Limites de transação
   
2. **Verificar documentação atualizada** da API WitePay

3. **Considerar API alternativa temporária** se necessário

---

## 🔧 Implementação Imediata

O arquivo **VPS_DEFINITIVO_APP.py** atualizado já contém todas as correções. Basta substituir na VPS e reiniciar para testar a solução.

A correção implementa múltiplas tentativas e logs detalhados para identificar exatamente onde está o problema na geração do QR code PIX.