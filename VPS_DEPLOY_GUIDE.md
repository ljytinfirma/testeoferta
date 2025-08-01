# 🚀 Guia de Deploy VPS - ENCCEJA 2025 CORRIGIDO

## 📋 Resumo das Correções

✅ **Página principal é `/inscricao`** - Redireciona automaticamente  
✅ **API de CPF funcionando** - Estrutura de dados corrigida  
✅ **Sem redirecionamento G1** - Acesso liberado para desktop e mobile  
✅ **Apenas WitePay** - Sistema de pagamento unificado  
✅ **Compatibilidade VPS** - Headers e timeouts ajustados  

---

## 📁 Arquivos para Upload

### 1. Arquivo Principal da Aplicação
```bash
# Substituir o app.py atual
cp VPS_FINAL_APP.py app.py
```

### 2. Gateway de Pagamento
```bash  
# Substituir ou criar witepay_gateway.py
cp VPS_FINAL_WITEPAY.py witepay_gateway.py
```

### 3. Variáveis de Ambiente
```bash
# Criar .env com as configurações
cat VPS_FINAL_ENV.txt > .env
```

### 4. Main.py (mantém igual)
```python
from app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 5. Requirements.txt
```txt
Flask==3.0.3
gunicorn==23.0.0
python-dotenv==1.0.1
requests==2.32.3
qrcode[pil]==7.4.2
```

---

## 🔧 Comandos para VPS

### 1. Conectar via MobaXterm SSH
```bash
ssh root@seu-servidor-ip
```

### 2. Navegar para pasta do projeto
```bash
cd /var/www/encceja
```

### 3. Backup dos arquivos atuais
```bash
cp app.py app_backup_$(date +%Y%m%d).py
cp witepay_gateway.py witepay_backup_$(date +%Y%m%d).py 2>/dev/null || true
```

### 4. Fazer upload dos novos arquivos
**Via MobaXterm:**
- Arraste `VPS_FINAL_APP.py` → renomeie para `app.py`
- Arraste `VPS_FINAL_WITEPAY.py` → renomeie para `witepay_gateway.py`  
- Crie `.env` com conteúdo de `VPS_FINAL_ENV.txt`

### 5. Verificar dependências
```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 6. Testar aplicação local
```bash
python main.py
```
**Saída esperada:** `Running on http://0.0.0.0:5000`

### 7. Testar API de CPF
```bash
curl "http://localhost:5000/consultar-cpf-inscricao?cpf=11542036704"
```
**Saída esperada:** `{"cpf":"11542036704","nome":"GABRIEL DE OLIVEIRA NOVAES",...}`

### 8. Reiniciar serviços
```bash
sudo supervisorctl restart encceja
sudo systemctl reload nginx
```

### 9. Verificar status
```bash
sudo supervisorctl status
```

---

## 🌐 Testes de Funcionamento

### 1. Página Principal
- `http://seu-dominio.com/` → Deve redirecionar para `/inscricao`
- `http://seu-dominio.com/inscricao` → Página ENCCEJA carregada

### 2. API de CPF
- Digite CPF na página
- Deve retornar dados sem erro "Ocorreu um erro ao validar o CPF"
- Exemplo testado: CPF 11542036704 = GABRIEL DE OLIVEIRA NOVAES

### 3. Sistema de Pagamento
- Após preencher dados, ir para pagamento
- Deve gerar QR Code PIX de R$ 93,40

---

## 🔍 Resolução de Problemas

### Erro "Ocorreu um erro ao validar o CPF"
```bash
# Verificar logs
tail -f /var/log/supervisor/encceja.log

# Testar API manualmente
curl "http://localhost:5000/consultar-cpf-inscricao?cpf=11542036704"
```

### Redirecionamento para G1
- Verificar se o template `inscricao.html` foi atualizado
- JavaScript deve ter verificação comentada

### Erro de importação WitePay
```bash
# Verificar se arquivo existe
ls -la witepay_gateway.py

# Verificar sintaxe
python -c "import witepay_gateway; print('OK')"
```

---

## 📊 Monitoramento

### Logs da Aplicação
```bash
tail -f /var/log/supervisor/encceja.log
```

### Logs do Nginx
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Status dos Serviços
```bash
sudo supervisorctl status
sudo systemctl status nginx
```

---

## ✅ Checklist Final

- [ ] Arquivo `app.py` substituído com `VPS_FINAL_APP.py`
- [ ] Arquivo `witepay_gateway.py` criado com `VPS_FINAL_WITEPAY.py`  
- [ ] Arquivo `.env` configurado com as variáveis corretas
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Aplicação testada localmente (`python main.py`)
- [ ] API de CPF testada e funcionando
- [ ] Supervisor reiniciado (`sudo supervisorctl restart encceja`)
- [ ] Nginx reiniciado (`sudo systemctl reload nginx`)
- [ ] Página principal redirecionando para `/inscricao`
- [ ] Sistema de pagamento funcionando

---

## 🎯 Resultado Esperado

Após seguir este guia:
1. **Página principal**: `seu-dominio.com` → redireciona para `/inscricao`
2. **API CPF funcionando**: Consulta retorna dados reais
3. **Sem redirecionamento G1**: Acesso normal em desktop e mobile  
4. **Pagamentos PIX**: R$ 93,40 via WitePay funcionando
5. **Sistema estável**: Logs limpos, sem erros

A aplicação ficará **100% funcional** no VPS com todas as correções aplicadas!