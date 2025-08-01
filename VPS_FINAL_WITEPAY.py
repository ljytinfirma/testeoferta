import os
import requests
from datetime import datetime
from flask import current_app
from typing import Dict, Optional

def create_witepay_payment(amount: float, description: str) -> Dict:
    """
    Criar um pagamento PIX via WitePay API
    """
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            current_app.logger.error("WITEPAY_API_KEY não encontrada")
            return {'success': False, 'error': 'API key não configurada'}
        
        # Dados padronizados para o pagamento
        order_data = {
            "email": "gerarpagamentos@gmail.com",
            "phone": "(11) 98779-0088",
            "name": "Receita do Amor",
            "document": "11.111.111/0001-11",
            "amount": int(amount * 100),  # Converter para centavos
            "currency": "BRL",
            "items": [
                {
                    "title": description,
                    "quantity": 1,
                    "unit_price": int(amount * 100)
                }
            ]
        }
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Criar ordem
        order_response = requests.post(
            'https://api.witepay.com/v1/order/create',
            json=order_data,
            headers=headers,
            timeout=30
        )
        
        if order_response.status_code != 200:
            current_app.logger.error(f"Erro ao criar ordem: {order_response.status_code} - {order_response.text}")
            return {'success': False, 'error': 'Erro ao criar ordem'}
        
        order_result = order_response.json()
        order_id = order_result.get('id')
        
        if not order_id:
            current_app.logger.error(f"ID da ordem não encontrado: {order_result}")
            return {'success': False, 'error': 'ID da ordem não encontrado'}
        
        # Criar cobrança PIX
        charge_data = {
            "payment_method": "pix",
            "order_id": order_id
        }
        
        charge_response = requests.post(
            'https://api.witepay.com/v1/charge/create',
            json=charge_data,
            headers=headers,
            timeout=30
        )
        
        if charge_response.status_code != 200:
            current_app.logger.error(f"Erro ao criar cobrança: {charge_response.status_code} - {charge_response.text}")
            return {'success': False, 'error': 'Erro ao criar cobrança'}
        
        charge_result = charge_response.json()
        
        # Extrair dados da resposta
        payment_data = charge_result.get('payment', {})
        pix_data = payment_data.get('pix', {})
        
        result = {
            'success': True,
            'transaction_id': charge_result.get('id'),
            'order_id': order_id,
            'pix_code': pix_data.get('qr_code_text', ''),
            'qr_code': pix_data.get('qr_code_text', ''),  # Compatibilidade
            'amount': amount,
            'status': charge_result.get('status', 'pending'),
            'created_at': datetime.now().isoformat()
        }
        
        current_app.logger.info(f"Pagamento PIX criado com sucesso: {result['transaction_id']}")
        return result
        
    except Exception as e:
        current_app.logger.error(f"Erro ao criar pagamento WitePay: {str(e)}")
        return {'success': False, 'error': f'Erro interno: {str(e)}'}

def check_payment_status(transaction_id: str) -> Dict:
    """
    Verificar status de um pagamento no WitePay
    """
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            return {'status': 'error', 'paid': False, 'error': 'API key não configurada'}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Consultar status da cobrança
        response = requests.get(
            f'https://api.witepay.com/v1/charge/{transaction_id}',
            headers=headers,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'pending').lower()
            
            # Mapear status do WitePay para nosso formato
            is_paid = status in ['paid', 'completed', 'approved', 'confirmed']
            
            return {
                'status': status,
                'paid': is_paid,
                'transaction_id': transaction_id,
                'amount': data.get('amount', 0) / 100 if data.get('amount') else 0
            }
        else:
            current_app.logger.error(f"Erro ao consultar status: {response.status_code}")
            return {'status': 'error', 'paid': False, 'error': 'Erro na consulta'}
            
    except Exception as e:
        current_app.logger.error(f"Erro ao verificar status do pagamento: {str(e)}")
        return {'status': 'error', 'paid': False, 'error': str(e)}