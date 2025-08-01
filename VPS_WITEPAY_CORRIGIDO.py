import os
import requests
import json
import logging
from datetime import datetime
from typing import Dict, Optional

def create_witepay_payment(amount: float, description: str = "Inscrição ENCCEJA 2025") -> Dict:
    """
    Criar um pagamento PIX via WitePay API - Versão VPS corrigida
    """
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            logging.error("WITEPAY_API_KEY não encontrada")
            return {'success': False, 'error': 'API key não configurada'}
        
        # Dados padronizados para o pagamento ENCCEJA
        order_data = {
            "productData": [
                {
                    "name": description,
                    "value": int(amount * 100)  # Converter para centavos (93.40 -> 9340)
                }
            ],
            "clientData": {
                "clientName": "Receita do Amor",
                "clientDocument": "11111111000111",  # CPF/CNPJ apenas números
                "clientEmail": "gerarpagamentos@gmail.com",
                "clientPhone": "11987790088"  # Telefone apenas números
            }
        }
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        logging.info(f"Criando ordem WitePay - Valor: R$ {amount:.2f}")
        
        # Passo 1: Criar ordem
        order_response = requests.post(
            'https://api.witepay.com.br/v1/order/create',
            json=order_data,
            headers=headers,
            timeout=30
        )
        
        logging.info(f"Status ordem: {order_response.status_code}")
        
        if order_response.status_code not in [200, 201]:
            logging.error(f"Erro ao criar ordem: {order_response.status_code} - {order_response.text}")
            return {'success': False, 'error': f'Erro ao criar ordem: {order_response.status_code}'}
        
        order_result = order_response.json()
        order_id = order_result.get('orderId')
        
        if not order_id:
            logging.error(f"ID da ordem não encontrado: {order_result}")
            return {'success': False, 'error': 'ID da ordem não encontrado'}
        
        logging.info(f"Ordem criada com sucesso: {order_id}")
        
        # Passo 2: Criar cobrança PIX
        charge_data = {
            "paymentMethod": "PIX",
            "orderId": order_id
        }
        
        charge_response = requests.post(
            'https://api.witepay.com.br/v1/charge/create',
            json=charge_data,
            headers=headers,
            timeout=30
        )
        
        logging.info(f"Status cobrança: {charge_response.status_code}")
        
        if charge_response.status_code not in [200, 201]:
            logging.error(f"Erro ao criar cobrança: {charge_response.status_code} - {charge_response.text}")
            return {'success': False, 'error': f'Erro ao criar cobrança: {charge_response.status_code}'}
        
        charge_result = charge_response.json()
        
        # Extrair dados do PIX
        pix_code = charge_result.get('pixCode') or charge_result.get('pix_code')
        qr_code = charge_result.get('pixQrCode') or charge_result.get('qr_code')
        transaction_id = charge_result.get('chargeId') or charge_result.get('id') or order_id
        
        if not pix_code:
            logging.error(f"Código PIX não encontrado: {charge_result}")
            return {'success': False, 'error': 'Código PIX não encontrado'}
        
        logging.info(f"Pagamento PIX criado com sucesso - ID: {transaction_id}")
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'pix_code': pix_code,
            'qr_code': qr_code,
            'amount': amount,
            'order_id': order_id,
            'expires_at': charge_result.get('expiresAt'),
            'status': 'pending'
        }
        
    except requests.exceptions.Timeout:
        logging.error("Timeout na requisição WitePay")
        return {'success': False, 'error': 'Timeout na requisição'}
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro de conexão WitePay: {e}")
        return {'success': False, 'error': 'Erro de conexão'}
    except Exception as e:
        logging.error(f"Erro inesperado WitePay: {e}")
        return {'success': False, 'error': f'Erro interno: {str(e)}'}

def check_payment_status(transaction_id: str) -> Dict:
    """
    Verificar status do pagamento WitePay
    """
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            return {'status': 'pending', 'paid': False}
        
        headers = {
            'x-api-key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Verificar status da cobrança
        response = requests.get(
            f'https://api.witepay.com.br/v1/charge/{transaction_id}',
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', '').upper()
            
            # Status conhecidos do WitePay
            if status in ['PAID', 'COMPLETED', 'APPROVED']:
                return {'status': 'paid', 'paid': True}
            elif status in ['CANCELED', 'REJECTED', 'FAILED']:
                return {'status': 'failed', 'paid': False}
            else:
                return {'status': 'pending', 'paid': False}
        
        return {'status': 'pending', 'paid': False}
        
    except Exception as e:
        logging.error(f"Erro ao verificar status: {e}")
        return {'status': 'pending', 'paid': False}