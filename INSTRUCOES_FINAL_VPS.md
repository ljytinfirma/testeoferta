# 🚀 INSTRUÇÕES FINAIS - DEPLOY VPS HOSTINGER

## ✅ STATUS ATUAL

**✓ Chave WitePay configurada e testada**  
**✓ Sistema funcionando no Replit**  
**✓ Código VPS pronto para produção**  
**✓ PIX R$ 93,40 gerado com sucesso**

---

## 📦 ARQUIVO FINAL VPS

**Arquivo principal:** `VPS_FINAL_DEPLOYMENT_COMPLETE.py`

### ⚡ Recursos Implementados:

1. **WitePay Integrado:**
   - Chave privada: `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`
   - Chave pública: `pk_0b40ad65659b5575c87cb4adf56c7f29`
   - Valor fixo: R$ 93,40

2. **Fluxo Completo:**
   - `/` → `/inscricao` (redirecionamento automático)
   - Consulta CPF na API externa
   - Páginas: encceja-info → validar-dados → endereco → local-prova → pagamento
   - Geração PIX instantânea

3. **Tratamento de Erros:**
   - Logs detalhados com prefixo `[VPS]`
   - Fallback para problemas de QR code
   - Múltiplas tentativas de geração PIX

4. **Configuração VPS:**
   - Logs salvos em `/var/log/encceja-app.log`
   - Chaves hardcoded (não dependem de .env)
   - Porta 5000 configurada
   - Debug desabilitado para produção

---

## 🔧 INSTALAÇÃO NA VPS

### 1. Conectar VPS via SSH
```bash
ssh root@SEU_IP_HOSTINGER
```

### 2. Preparar ambiente
```bash
# Navegar para diretório da aplicação
cd /var/www/encceja

# Backup do arquivo atual
mv app.py app.py.backup

# Fazer upload do novo arquivo
# (Usar MobaXterm para enviar VPS_FINAL_DEPLOYMENT_COMPLETE.py)
```

### 3. Renomear e configurar
```bash
# Renomear arquivo
mv VPS_FINAL_DEPLOYMENT_COMPLETE.py app.py

# Dar permissões
chmod +x app.py

# Verificar dependências (devem estar instaladas)
pip3 list | grep -E "(flask|requests|qrcode)"
```

### 4. Testar funcionamento
```bash
# Testar a aplicação
python3 app.py

# Em outro terminal, testar pagamento
curl -X POST "http://localhost:5000/criar-pagamento-pix" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Resultado esperado:**
```json
{
  "success": true,
  "id": "ch_xxxxx",
  "pix_code": "00020101021226840014br.gov.bcb.pix...",
  "amount": 93.4
}
```

### 5. Reiniciar serviços
```bash
# Parar servidor de teste
Ctrl+C

# Reiniciar via Supervisor
sudo supervisorctl restart encceja

# Verificar status
sudo supervisorctl status encceja

# Verificar logs
tail -f /var/log/supervisor/encceja.log
```

---

## 🧪 TESTE FINAL COMPLETO

### 1. Acessar aplicação:
```
http://SEU_IP_VPS:5000
```

### 2. Fluxo de teste:
1. **Página inicial** → Redirecionamento automático
2. **Inscrição:** Inserir CPF `11111111111`
3. **ENCCEJA Info:** Clicar "Prosseguir"
4. **Validar Dados:** Confirmar informações
5. **Endereço:** Preencher dados
6. **Local Prova:** Selecionar local
7. **Pagamento:** PIX R$ 93,40 deve aparecer

### 3. Verificação do PIX:
- QR Code visível na tela
- Valor: R$ 93,40
- Código PIX com 200+ caracteres
- Botão "Copiar código PIX" funcionando

---

## 📋 CHECKLIST FINAL

**Antes de finalizar:**

- [ ] SSH funcionando na VPS
- [ ] Arquivo `VPS_FINAL_DEPLOYMENT_COMPLETE.py` enviado
- [ ] Renomeado para `app.py`
- [ ] Supervisor reiniciado
- [ ] Teste de pagamento PIX OK
- [ ] Logs sem erros críticos
- [ ] Fluxo completo funcionando

**Após deployment:**

- [ ] Acesso via navegador OK
- [ ] CPF `11111111111` consulta dados
- [ ] Todas as páginas carregando
- [ ] PIX gerado corretamente
- [ ] Valor R$ 93,40 correto
- [ ] QR Code visível

---

## 🎯 RESOLUÇÃO DE PROBLEMAS

### Se der erro 500:
```bash
# Verificar logs detalhados
tail -20 /var/log/supervisor/encceja.log

# Verificar sintaxe Python
python3 -m py_compile app.py
```

### Se PIX não gerar:
```bash
# Testar WitePay direto
curl -X POST "https://api.witepay.com.br/v1/order/create" \
  -H "x-api-key: sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d" \
  -H "Content-Type: application/json" \
  -d '{"productData":[{"name":"Teste","value":9340}],"clientData":{"clientName":"Teste","clientDocument":"11111111000111","clientEmail":"teste@gmail.com","clientPhone":"11987790088"}}'
```

### Se aplicação não iniciar:
```bash
# Verificar porta
netstat -tlnp | grep :5000

# Verificar processo
ps aux | grep python
```

---

## 🏆 RESULTADO FINAL

**Após seguir estas instruções:**

✅ **Sistema ENCCEJA funcionando 100% na VPS Hostinger**  
✅ **PIX R$ 93,40 gerado via WitePay em produção**  
✅ **Fluxo completo de inscrição operacional**  
✅ **Logs detalhados para monitoramento**  
✅ **Tratamento de erros robusto**

**O sistema está pronto para receber usuários reais na VPS!**