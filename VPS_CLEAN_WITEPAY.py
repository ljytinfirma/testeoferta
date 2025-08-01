import os
import requests
from datetime import datetime
from flask import current_app
from typing import Dict, Any

def create_witepay_payment(amount: float, product_name: str = "Inscrição ENCCEJA 2025") -> Dict[str, Any]:
    """
    Cria pagamento PIX via WitePay API
    """
    api_key = os.environ.get("WITEPAY_API_KEY", "wtp_7819b0bb469f4b52a96feca4ddc46ba4")
    
    # Dados do pedido
    order_data = {
        "amount": int(amount * 100),  # Converter para centavos
        "currency": "BRL",
        "customer": {
            "name": "Usuario ENCCEJA",
            "email": "gerarpagamentos@gmail.com", 
            "phone": "(11) 98779-0088"
        },
        "items": [{
            "title": product_name,
            "quantity": 1,
            "amount": int(amount * 100)
        }]
    }
    
    try:
        # Criar pedido
        order_response = requests.post(
            "https://api.witepay.com/v1/order/create",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=order_data,
            timeout=30
        )
        
        if order_response.status_code == 200:
            order = order_response.json()
            order_id = order.get("data", {}).get("id")
            
            # Criar cobrança PIX
            charge_data = {
                "order_id": order_id,
                "payment_method": "PIX"
            }
            
            charge_response = requests.post(
                "https://api.witepay.com/v1/charge/create",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json=charge_data,
                timeout=30
            )
            
            if charge_response.status_code == 200:
                charge = charge_response.json()
                charge_data = charge.get("data", {})
                
                return {
                    "success": True,
                    "transaction_id": charge_data.get("id"),
                    "pix_code": charge_data.get("pix_code"),
                    "qr_code": charge_data.get("pix_code"),
                    "amount": amount,
                    "status": "pending"
                }
    
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro WitePay: {e}")
    
    # Fallback em caso de erro
    return {
        "success": False,
        "error": "Erro ao gerar pagamento PIX"
    }

def check_payment_status(transaction_id: str) -> Dict[str, Any]:
    """
    Verifica status do pagamento
    """
    api_key = os.environ.get("WITEPAY_API_KEY")
    
    try:
        response = requests.get(
            f"https://api.witepay.com/v1/charge/{transaction_id}",
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json().get("data", {})
            return {
                "status": data.get("status", "pending"),
                "paid": data.get("status") in ["PAID", "COMPLETED", "APPROVED"]
            }
    
    except Exception as e:
        if current_app:
            current_app.logger.error(f"Erro verificação status: {e}")
    
    return {"status": "pending", "paid": False}