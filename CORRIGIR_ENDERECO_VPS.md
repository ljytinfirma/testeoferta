# 🔧 Correção Página /endereco na VPS

## ❌ Problema Identificado
A página `/endereco` estava retornando "Not Found" porque a rota não estava conectada com os dados da sessão do usuário.

## ✅ Solução Implementada
Atualizar o arquivo `app.py` na VPS com a rota `/endereco` corrigida.

---

## 🚀 Passos para Corrigir na VPS

### 1️⃣ Conectar na VPS
```bash
# Abrir MobaXterm
# Session → SSH
# Host: SEU_IP_VPS
# User: root
```

### 2️⃣ Navegar para o projeto
```bash
cd /var/www/encceja
```

### 3️⃣ Fazer backup do arquivo atual
```bash
cp app.py app_backup_endereco_$(date +%Y%m%d).py
```

### 4️⃣ Editar o arquivo app.py
```bash
nano app.py
```

### 5️⃣ Localizar a rota /endereco (linha ~1594)
Procure por:
```python
@app.route('/endereco')
def endereco():
    """Página de cadastro de endereço"""
    return render_template('endereco.html')
```

### 6️⃣ Substituir pela versão corrigida
Substitua por:
```python
@app.route('/endereco', methods=['GET', 'POST'])
def endereco():
    """Página de cadastro de endereço"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Atualizar dados do usuário com endereço
        user_data.update({
            'cep': request.form.get('cep', ''),
            'logradouro': request.form.get('logradouro', ''),
            'numero': request.form.get('numero', ''),
            'complemento': request.form.get('complemento', ''),
            'bairro': request.form.get('bairro', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', ''),
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', '')
        })
        session['user_data'] = user_data
        return redirect(url_for('pagamento_encceja'))
    
    return render_template('endereco.html', user_data=user_data)
```

### 7️⃣ Salvar e sair
```bash
# No nano:
# Ctrl + X
# Y (para confirmar)
# Enter (para salvar)
```

### 8️⃣ Testar alteração
```bash
python main.py
```

**Saída esperada:**
```
* Running on http://0.0.0.0:5000
* Debug mode: on
```

### 9️⃣ Testar rota (em outro terminal)
```bash
curl "http://localhost:5000/endereco"
```

**Resultado esperado:** HTML da página de endereço

### 🔟 Reiniciar serviços de produção
```bash
# Parar teste com Ctrl+C
sudo supervisorctl restart encceja
sudo systemctl reload nginx
```

### 1️⃣1️⃣ Verificar status
```bash
sudo supervisorctl status
```

**Saída esperada:**
```
encceja    RUNNING   pid 1234, uptime 0:00:05
```

---

## 🧪 Teste Final no Navegador

1. **Acesse:** `http://seu-dominio.com/inscricao`
2. **Digite CPF:** `115.420.367-04`
3. **Selecione imagem** da folha (5ª opção)
4. **Clique "Enviar"**
5. **Vá para endereço:** `http://seu-dominio.com/endereco`
6. **Resultado:** Página deve carregar normalmente com os dados do usuário

---

## ⚠️ Alternativa Rápida: Upload do Arquivo Corrigido

Se preferir, pode usar o arquivo `VPS_FINAL_APP.py` que já tem todas as correções:

```bash
# No MobaXterm, arraste VPS_FINAL_APP.py para a pasta
# Depois renomeie:
mv VPS_FINAL_APP.py app.py
sudo supervisorctl restart encceja
```

---

## ✅ Confirmação de Sucesso

Após a correção:
- ✅ `/endereco` não retorna mais "Not Found"
- ✅ Página carrega com dados do usuário
- ✅ Formulário funciona e redireciona para pagamento
- ✅ Sistema integrado com sessão do usuário

A correção resolve o problema e mantém o fluxo de inscrição funcionando perfeitamente!