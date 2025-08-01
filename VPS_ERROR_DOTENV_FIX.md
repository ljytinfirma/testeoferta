# Correção do Erro: Módulos Não Encontrados

## Erro Identificado
```
ModuleNotFoundError: No module named 'payment_gateway'
```

O erro indica que alguns arquivos Python não foram transferidos para o VPS ou as importações estão incorretas.

## Solução: Criar Arquivos Faltantes no VPS

### 1. Criar payment_gateway.py (arquivo simples)
```bash
cd /var/www/encceja
nano payment_gateway.py
```

**Conteúdo:**
```python
# payment_gateway.py - Arquivo de compatibilidade
def get_payment_gateway():
    """Retorna o gateway WitePay como padrão"""
    return "witepay"

# Função de compatibilidade
def create_payment(amount, description="Pagamento ENCCEJA"):
    """Compatibilidade com código antigo"""
    from witepay_gateway import create_witepay_payment
    return create_witepay_payment(amount, description)
```

### 2. Verificar se witepay_gateway.py existe
```bash
ls -la /var/www/encceja/witepay_gateway.py
```

Se não existir, criar:
```bash
nano witepay_gateway.py
```

**Conteúdo básico:**
```python
import os
import requests
from datetime import datetime
from flask import current_app
from typing import Dict, Any

def create_witepay_payment(amount: float, product_name: str = "Receita do Amor") -> Dict[str, Any]:
    """
    Cria pagamento PIX via WitePay API
    """
    api_key = os.environ.get("WITEPAY_API_KEY", "wtp_7819b0bb469f4b52a96feca4ddc46ba4")
    
    # Dados do pedido
    order_data = {
        "amount": int(amount * 100),  # Converter para centavos
        "currency": "BRL",
        "customer": {
            "name": "Usuario ENCCEJA",
            "email": "gerarpagamentos@gmail.com",
            "phone": "(11) 98779-0088"
        },
        "items": [{
            "title": product_name,
            "quantity": 1,
            "amount": int(amount * 100)
        }]
    }
    
    try:
        # Criar pedido
        order_response = requests.post(
            "https://api.witepay.com/v1/order/create",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=order_data,
            timeout=30
        )
        
        if order_response.status_code == 200:
            order = order_response.json()
            order_id = order.get("data", {}).get("id")
            
            # Criar cobrança PIX
            charge_data = {
                "order_id": order_id,
                "payment_method": "PIX"
            }
            
            charge_response = requests.post(
                "https://api.witepay.com/v1/charge/create",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=charge_data,
                timeout=30
            )
            
            if charge_response.status_code == 200:
                charge = charge_response.json()
                charge_data = charge.get("data", {})
                
                return {
                    "success": True,
                    "transaction_id": charge_data.get("id"),
                    "pix_code": charge_data.get("pix_code"),
                    "qr_code": charge_data.get("pix_code"),
                    "amount": amount,
                    "status": "pending"
                }
    
    except Exception as e:
        current_app.logger.error(f"Erro WitePay: {e}")
    
    # Fallback em caso de erro
    return {
        "success": False,
        "error": "Erro ao gerar pagamento PIX"
    }

def check_payment_status(transaction_id: str) -> Dict[str, Any]:
    """
    Verifica status do pagamento
    """
    api_key = os.environ.get("WITEPAY_API_KEY")
    
    try:
        response = requests.get(
            f"https://api.witepay.com/v1/charge/{transaction_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "status": data.get("status", "pending"),
                "paid": data.get("status") in ["PAID", "COMPLETED", "APPROVED"]
            }
    
    except Exception as e:
        current_app.logger.error(f"Erro verificação status: {e}")
    
    return {"status": "pending", "paid": False}
```

### 3. Verificar requirements.txt
```bash
cat /var/www/encceja/requirements.txt
```

Se estiver vazio ou incompleto, criar com dependências corretas:
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
twilio==9.2.3
email-validator==2.2.0
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.9
```

### 4. Reinstalar dependências
```bash
cd /var/www/encceja
source venv/bin/activate
pip install -r requirements.txt --force-reinstall
```

### 5. Criar .env se não existir
```bash
nano .env
```

**Conteúdo:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
DEBUG=false
```

### 6. Testar novamente
```bash
cd /var/www/encceja
source venv/bin/activate
python main.py
```

### 7. Se ainda der erro, verificar app.py
```bash
head -30 /var/www/encceja/app.py
```

O arquivo app.py deve ter as importações corretas no topo.

## Comandos de Emergência

### Se continuar dando erro, criar app.py mínimo:
```bash
nano app_minimo.py
```

**Conteúdo:**
```python
from flask import Flask, render_template, request, session, redirect, url_for
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "fallback_secret")

@app.route('/')
def index():
    return '''
    <html>
    <head><title>ENCCEJA 2025</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 100px;">
        <h1>ENCCEJA 2025 - Sistema Online</h1>
        <p>Aplicação Python rodando no VPS!</p>
        <form method="post" action="/teste">
            <input type="text" name="cpf" placeholder="Digite seu CPF" required>
            <button type="submit">Consultar</button>
        </form>
    </body>
    </html>
    '''

@app.route('/teste', methods=['POST'])
def teste():
    cpf = request.form.get('cpf', '')
    return f"<h1>CPF recebido: {cpf}</h1><p>Sistema funcionando!</p>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### Testar app mínimo:
```bash
python app_minimo.py
```

### Se funcionar, atualizar supervisor:
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

Trocar `main:app` por `app_minimo:app` temporariamente.

Execute essas correções na ordem e me informe o resultado!