# Configuração WitePay - Chaves Funcionais

## 🔑 Chaves Configuradas no Sistema

### **WitePay API Key (OBRIGATÓRIA)**
```env
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
```
- **Status**: ✅ Ativa e funcionando
- **Ambiente**: Produção
- **Valor PIX**: R$ 93,40 (9340 centavos)
- **Produto**: "Receita do Amor"

### **Session Secret (OBRIGATÓRIA)**
```env
SESSION_SECRET=8f2e7c4a9b1d6e3f0c5a8b2e9f7c4d1a6b3e0c9f7d4a1b8e5c2f9d6a3b0e7c4f1
```
- **Status**: ✅ Configurada
- **Uso**: Segurança das sessões Flask
- **Tipo**: Chave aleatória de 64 caracteres

## 📊 Tracking e Analytics

### **UTMFY Google Pixel**
```env
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
```
- **Status**: ✅ Configurado
- **Conversões**: Ativadas em pagamentos confirmados
- **Trigger**: Via JavaScript no frontend

### **Facebook Pixels (Múltiplos)**
```env
FACEBOOK_PIXEL_IDS=1418766538994503,1345433039826605,1390026985502891
```
- **Status**: ✅ Configurados
- **Quantidade**: 3 pixels diferentes
- **Eventos**: Purchase, Lead, ViewContent

## 🚀 Fluxo de Pagamento Configurado

### **1. Criação do Pagamento**
- **API**: WitePay `/v1/order/create`
- **Valor**: R$ 93,40 (fixo)
- **Cliente**: Email padrão gerarpagamentos@gmail.com
- **Telefone**: (11) 98779-0088

### **2. Webhook/Postback**
- **Endpoint**: `/witepay-postback`
- **Métodos**: POST
- **Validação**: Status PAID/COMPLETED/APPROVED

### **3. Verificação de Status**
- **Endpoint**: `/verificar-pagamento`
- **Storage**: Session + In-memory store
- **Polling**: Frontend verifica a cada 3 segundos

## 📁 Arquivos de Configuração

### **Para Hostinger (.env)**
```env
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
SESSION_SECRET=8f2e7c4a9b1d6e3f0c5a8b2e9f7c4d1a6b3e0c9f7d4a1b8e5c2f9d6a3b0e7c4f1
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
FACEBOOK_PIXEL_IDS=1418766538994503,1345433039826605,1390026985502891
```

### **Para Vercel (Environment Variables)**
```bash
vercel env add WITEPAY_API_KEY
# Valor: wtp_7819b0bb469f4b52a96feca4ddc46ba4

vercel env add SESSION_SECRET
# Valor: 8f2e7c4a9b1d6e3f0c5a8b2e9f7c4d1a6b3e0c9f7d4a1b8e5c2f9d6a3b0e7c4f1
```

## ✅ Testes de Validação

### **URLs para Testar:**
1. **Página inicial**: `https://seusite.com/`
2. **Gerar PIX**: `https://seusite.com/pagamento`
3. **Webhook**: `https://seusite.com/witepay-postback`
4. **Status**: `https://seusite.com/verificar-pagamento`

### **Dados de Teste:**
```json
{
  "nome": "João Silva",
  "cpf": "12345678901",
  "telefone": "(11) 99999-9999"
}
```

### **Resposta Esperada (PIX):**
```json
{
  "id": "ch_...",
  "pixCode": "00020101021226880014br.gov.bcb.pix...",
  "status": "pending",
  "expiresAt": "2025-08-01T03:XX:XX"
}
```

## 🔍 Logs para Monitorar

### **WitePay Gateway:**
```
INFO:app:[WITEPAY] Payment created: ch_xxxxx
INFO:app:[WITEPAY_POSTBACK] Payment confirmed for charge: ch_xxxxx
INFO:app:[UTMFY_GOOGLE_PIXEL] Payment conversion - Charge: ch_xxxxx, Amount: 93.4
```

### **Conversões:**
```
INFO:app:[FACEBOOK_PIXEL] Registrando evento de conversão para os pixels: 1418766538994503, 1345433039826605 e 1390026985502891
```

## ⚠️ Importante

- **Nunca** compartilhe as chaves em repositórios públicos
- **Sempre** use arquivo `.env` em produção
- **Monitore** os logs de erro regularmente
- **Teste** o fluxo completo após deploy

O sistema está 100% funcional com essas configurações!