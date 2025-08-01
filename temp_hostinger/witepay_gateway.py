import os
import requests
import logging
from typing import Dict, Any
from flask import current_app

class WitePayGateway:
    """
    WitePay Payment Gateway Integration
    Handles order creation and PIX payment generation
    """
    
    def __init__(self):
        self.api_key = os.environ.get('WITEPAY_API_KEY')
        self.api_base_url = "https://api.witepay.com.br/v1"
        
        if not self.api_key:
            raise ValueError("WITEPAY_API_KEY environment variable is required")
        
        if current_app:
            current_app.logger.info("WitePay gateway inicializado com sucesso")
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        return {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def create_order(self, client_data: Dict[str, Any], product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new order in WitePay
        
        Args:
            client_data: Dict with clientName, clientDocument, clientEmail, clientPhone
            product_data: Dict with name and value (in centavos)
        
        Returns:
            Dict with order information including orderId
        """
        try:
            # Prepare order payload
            order_payload = {
                "productData": [
                    {
                        "name": product_data.get('name', 'Receita do Amor'),
                        "value": product_data.get('value', 13842)  # Value in centavos
                    }
                ],
                "clientData": {
                    "clientName": client_data.get('clientName'),
                    "clientDocument": client_data.get('clientDocument'),  # CPF without dots and dashes
                    "clientEmail": client_data.get('clientEmail', 'gerarpagamentos@gmail.com'),
                    "clientPhone": client_data.get('clientPhone', '11987790088')  # DDD + number, only numbers
                }
            }
            
            current_app.logger.info(f"Criando pedido WitePay para cliente: {client_data.get('clientName')}")
            current_app.logger.debug(f"Order payload: {order_payload}")
            
            # Make API request to create order
            response = requests.post(
                f"{self.api_base_url}/order/create",
                json=order_payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            current_app.logger.info(f"WitePay order response status: {response.status_code}")
            current_app.logger.debug(f"Order response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                order_data = response.json()
                current_app.logger.info(f"Pedido criado com sucesso: {order_data.get('orderId', 'N/A')}")
                current_app.logger.debug(f"Full order data: {order_data}")
                return {
                    'success': True,
                    'orderId': order_data.get('orderId'),
                    'data': order_data
                }
            else:
                error_msg = f"Erro ao criar pedido: {response.status_code} - {response.text}"
                current_app.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Erro inesperado ao criar pedido: {str(e)}"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def create_pix_charge(self, order_id: str, webhook_url: str = None) -> Dict[str, Any]:
        """
        Create a PIX charge for an existing order
        
        Args:
            order_id: The order ID returned from create_order
            webhook_url: Optional webhook URL for payment notifications
        
        Returns:
            Dict with PIX payment information including QR code and copy-paste code
        """
        try:
            # Prepare charge payload
            charge_payload = {
                "orderId": order_id,
                "paymentMethod": "pix"
            }
            
            # Add webhook URL if provided
            if webhook_url:
                charge_payload["webhookUrl"] = webhook_url
            
            current_app.logger.info(f"Criando cobrança PIX para pedido: {order_id}")
            current_app.logger.debug(f"Charge payload: {charge_payload}")
            
            # Make API request to create PIX charge
            response = requests.post(
                f"{self.api_base_url}/charge/create",
                json=charge_payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            current_app.logger.info(f"WitePay charge response status: {response.status_code}")
            current_app.logger.debug(f"Charge response text: {response.text}")
            
            if response.status_code == 200 or response.status_code == 201:
                charge_data = response.json()
                current_app.logger.info(f"Cobrança PIX criada com sucesso")
                current_app.logger.debug(f"Charge response data: {charge_data}")
                
                # Extract PIX data with correct field names from WitePay API
                pix_qr_code = charge_data.get('qrCode')  # WitePay returns as 'qrCode'
                pix_copy_paste = charge_data.get('qrCode')  # Use QR code as copy-paste since WitePay doesn't provide separate field
                charge_id = charge_data.get('chargeId')  # WitePay returns as 'chargeId'
                
                current_app.logger.info(f"Extracted data - QR: {bool(pix_qr_code)}, Copy: {bool(pix_copy_paste)}, ID: {charge_id}")
                
                return {
                    'success': True,
                    'charge_id': charge_id,
                    'pix_qr_code': pix_qr_code,
                    'pix_copy_paste': pix_copy_paste,
                    'expires_at': charge_data.get('expiresAt'),  # WitePay uses camelCase
                    'data': charge_data
                }
            else:
                error_msg = f"Erro ao criar cobrança PIX: {response.status_code} - {response.text}"
                current_app.logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg
                }
                
        except Exception as e:
            error_msg = f"Erro inesperado ao criar cobrança PIX: {str(e)}"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }
    
    def create_complete_pix_payment(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete flow: Create order and PIX charge in one call
        
        Args:
            user_data: Dict with nome, cpf, amount, email (optional), phone (optional)
        
        Returns:
            Dict with complete payment information
        """
        try:
            # Extract and validate user data
            nome = user_data.get('nome', '').strip()
            cpf = user_data.get('cpf', '').strip()
            amount = user_data.get('amount', 138.42)
            
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
            
            # Prepare client data
            client_data = {
                'clientName': nome,
                'clientDocument': cpf_clean,
                'clientEmail': user_data.get('email', 'gerarpagamentos@gmail.com'),
                'clientPhone': user_data.get('phone', '11987790088')
            }
            
            # Prepare product data
            product_data = {
                'name': 'Receita do Amor',
                'value': amount_centavos
            }
            
            current_app.logger.info(f"Iniciando processo completo de pagamento para: {nome} - R$ {amount}")
            
            # Step 1: Create order
            order_result = self.create_order(client_data, product_data)
            if not order_result.get('success'):
                return order_result
            
            order_id = order_result.get('orderId')
            if not order_id:
                return {
                    'success': False,
                    'error': 'ID do pedido não retornado pela API'
                }
            
            # Step 2: Create PIX charge
            charge_result = self.create_pix_charge(order_id)
            if not charge_result.get('success'):
                return charge_result
            
            # Return complete payment information
            return {
                'success': True,
                'id': charge_result.get('charge_id'),
                'pixCode': charge_result.get('pix_copy_paste'),
                'pixQrCode': charge_result.get('pix_qr_code'),
                'expiresAt': charge_result.get('expires_at'),
                'orderId': order_id,
                'status': 'pending'
            }
            
        except Exception as e:
            error_msg = f"Erro no processo completo de pagamento: {str(e)}"
            current_app.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

def create_witepay_gateway():
    """Factory function to create WitePay gateway instance"""
    return WitePayGateway()