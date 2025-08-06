import os
import requests
import logging
import base64
from typing import Dict, Any
from flask import current_app

class FreePayGateway:
    """
    FreePay Payment Gateway Integration
    Handles PIX transaction creation following FreePay API standards
    """
    
    def __init__(self):
        self.secret_key = os.environ.get('FREEPAY_SECRET_KEY', 'sk_live_pGalAgvdrYzpdoaBqmWJH3iOb2uqi9cA1jlJXTfEWfqwCw9a')
        self.company_id = os.environ.get('FREEPAY_COMPANY_ID', '8187dded-16f6-428a-bfe1-8917ec32f3e0')
        self.api_base_url = "https://api.freepaybr.com/functions/v1"
        
        if not self.secret_key:
            raise ValueError("FREEPAY_SECRET_KEY environment variable is required")
        
        if current_app:
            current_app.logger.info("FreePay gateway inicializado com sucesso")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests using Basic Auth"""
        # Create Basic Auth string as per documentation: Basic base64(SECRET_KEY:x)
        auth_string = f"{self.secret_key}:x"
        auth_b64 = base64.b64encode(auth_string.encode()).decode()
        
        return {
            'authorization': f'Basic {auth_b64}',
            'Content-Type': 'application/json',
            'accept': 'application/json'
        }
    
    def create_pix_transaction(self, user_data: Dict[str, Any], amount: float) -> Dict[str, Any]:
        """
        Create a PIX transaction using FreePay API
        
        Args:
            user_data: Dict with nome, cpf, email (optional), phone (optional)
            amount: Amount in BRL (e.g., 93.40)
        
        Returns:
            Dict with transaction information including PIX data
        """
        try:
            # Extract and validate user data
            nome = user_data.get('nome', '').strip()
            cpf = user_data.get('cpf', '').strip()
            
            if not nome or not cpf:
                return {
                    'success': False,
                    'error': 'Nome e CPF são obrigatórios'
                }
            
            # Clean CPF (remove dots and dashes)
            cpf_clean = ''.join(filter(str.isdigit, cpf))
            if len(cpf_clean) != 11:
                return {
                    'success': False,
                    'error': 'CPF deve conter 11 dígitos'
                }
            
            # Convert amount to centavos (round to handle floating point precision)
            amount_centavos = round(float(amount) * 100)
            
            # Prepare transaction payload according to FreePay API documentation
            transaction_payload = {
                "customer": {
                    "name": nome,
                    "document": cpf_clean,
                    "email": user_data.get('email', 'gerarpagamentos@gmail.com'),
                    "phone": user_data.get('phone', '11987790088')
                },
                "paymentMethod": "PIX",
                "items": [
                    {
                        "name": "Taxa de Inscrição ENCCEJA 2025",
                        "quantity": 1,
                        "amount": amount_centavos
                    }
                ],
                "amount": amount_centavos
            }
            
            current_app.logger.info(f"Criando transação PIX FreePay para cliente: {nome}")
            current_app.logger.debug(f"Transaction payload: {transaction_payload}")
            
            # Make API request to create transaction
            response = requests.post(
                f"{self.api_base_url}/transactions",
                json=transaction_payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            current_app.logger.info(f"FreePay transaction response status: {response.status_code}")
            current_app.logger.debug(f"Transaction response text: {response.text}")
            
            if response.status_code == 200:
                transaction_data = response.json()
                current_app.logger.info(f"Transação PIX criada com sucesso")
                current_app.logger.debug(f"Transaction response data: {transaction_data}")
                
                # Extract PIX data from FreePay response structure
                pix_data = transaction_data.get('pix', {})
                pix_qr_code = pix_data.get('qrcode')  # FreePay retorna como 'qrcode' dentro do objeto 'pix'
                pix_copy_paste = pix_qr_code  # O QR code também serve como código copia e cola
                transaction_id = transaction_data.get('id')
                expires_at = pix_data.get('expirationDate')
                
                current_app.logger.info(f"Extracted data - QR: {bool(pix_qr_code)}, Copy: {bool(pix_copy_paste)}, ID: {transaction_id}")
                
                return {
                    'success': True,
                    'transaction_id': transaction_id,
                    'pix_qr_code': pix_qr_code,
                    'pix_copy_paste': pix_copy_paste,
                    'amount': amount,
                    'status': transaction_data.get('status', 'pending'),
                    'expires_at': expires_at,
                    'data': transaction_data
                }
            else:
                error_msg = f"Erro ao criar transação PIX: {response.status_code} - {response.text}"
                current_app.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Erro inesperado ao criar transação PIX: {str(e)}"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def create_complete_pix_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete PIX payment flow - simplified for FreePay (single API call)
        
        Args:
            user_data: Dict with nome, cpf, amount, email (optional), phone (optional)
        
        Returns:
            Dict with complete payment information
        """
        try:
            # Default amount
            amount = user_data.get('amount', 93.40)
            
            current_app.logger.info(f"Iniciando processo completo de pagamento FreePay para: {user_data.get('nome')} - R$ {amount}")
            
            # Create PIX transaction (single step with FreePay)
            transaction_result = self.create_pix_transaction(user_data, amount)
            
            if not transaction_result.get('success'):
                return transaction_result
            
            # Return complete payment information in the format expected by the application
            return {
                'success': True,
                'id': transaction_result.get('transaction_id'),
                'pixCode': transaction_result.get('pix_copy_paste'),
                'pixQrCode': transaction_result.get('pix_qr_code'),
                'expiresAt': transaction_result.get('expires_at'),
                'orderId': transaction_result.get('transaction_id'),  # FreePay uses single transaction ID
                'status': transaction_result.get('status', 'pending'),
                'amount': amount
            }
            
        except Exception as e:
            error_msg = f"Erro no processo completo de pagamento FreePay: {str(e)}"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

def check_payment_status(transaction_id):
    """
    Verifica o status de um pagamento PIX na FreePay
    """
    try:
        current_app.logger.info(f"[FREEPAY] Verificando status do pagamento: {transaction_id}")
        
        # Configurar headers com autenticação Basic
        secret_key = "sk_live_pGalAgvdrYzpdoaBqmWJH3iOb2uqi9cA1jlJXTfEWfqwCw9a"
        auth_string = base64.b64encode(f"{secret_key}:x".encode()).decode()
        
        headers = {
            'Authorization': f'Basic {auth_string}',
            'Content-Type': 'application/json'
        }
        
        # Endpoint para buscar transação específica
        url = f"https://api.freepaybr.com/functions/v1/transactions/{transaction_id}"
        
        current_app.logger.debug(f"[FREEPAY] Fazendo requisição GET para: {url}")
        
        response = requests.get(url, headers=headers, timeout=30)
        current_app.logger.info(f"FreePay status check response status: {response.status_code}")
        current_app.logger.debug(f"Status check response text: {response.text}")
        
        if response.status_code == 200:
            transaction_data = response.json()
            current_app.logger.info(f"Status da transação obtido com sucesso")
            
            # Extrair informações relevantes
            status = transaction_data.get('status')
            paid_at = transaction_data.get('paidAt')
            amount = transaction_data.get('amount', 0)
            customer = transaction_data.get('customer', {})
            pix_data = transaction_data.get('pix', {})
            
            current_app.logger.info(f"[FREEPAY] Status: {status}, Pago em: {paid_at}")
            
            return {
                'success': True,
                'transaction_id': transaction_id,
                'status': status,
                'paid': status == 'paid',
                'paid_at': paid_at,
                'amount': amount,
                'customer': customer,
                'pix_data': pix_data,
                'full_data': transaction_data
            }
        else:
            current_app.logger.error(f"[FREEPAY] Erro ao verificar status - HTTP {response.status_code}: {response.text}")
            return {
                'success': False,
                'error': f'Erro HTTP {response.status_code} ao verificar status do pagamento'
            }
            
    except Exception as e:
        current_app.logger.error(f"[FREEPAY] Erro ao verificar status: {str(e)}")
        return {
            'success': False,
            'error': f'Erro na comunicação com FreePay: {str(e)}'
        }

def create_freepay_gateway():
    """Factory function to create FreePay gateway instance"""
    return FreePayGateway()