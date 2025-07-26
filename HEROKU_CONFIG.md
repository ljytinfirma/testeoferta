# Configuração Heroku - Variáveis de Ambiente

Para configurar o sistema de pagamentos WitePay no Heroku, você precisa adicionar a seguinte variável de ambiente:

## Variáveis Obrigatórias

### WITEPAY_API_KEY
- **Valor**: `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`
- **Descrição**: Chave de API do WitePay para gerar cobranças PIX autênticas

## Como Configurar no Heroku

### Via Dashboard (Interface Web)
1. Acesse seu app no Heroku Dashboard
2. Vá em **Settings** → **Config Vars**
3. Clique em **Reveal Config Vars**
4. Adicione:
   - **KEY**: `WITEPAY_API_KEY`
   - **VALUE**: `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`
5. Clique em **Add**

### Via CLI (Linha de Comando)
```bash
heroku config:set WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d --app seu-app-name
```

## Verificação
Após configurar, o sistema irá:
- Gerar pagamentos PIX de R$ 93,40
- Criar QR codes funcionais
- Processar pagamentos através da API WitePay

## Outras Variáveis (Opcionais)
O sistema também suporta outras variáveis que já podem estar configuradas:
- `FOR4PAYMENTS_API_KEY`: Para pagamentos regionais na página /obrigado
- `SESSION_SECRET`: Para segurança das sessões (gerado automaticamente pelo Heroku)

---
*Arquivo criado em: 26/07/2025*