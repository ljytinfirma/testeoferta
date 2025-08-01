#!/usr/bin/env python3
"""
ENCCEJA 2025 - Aplicação Simples para Teste VPS
Use este arquivo para verificar se o ambiente básico funciona
"""

import sys
import logging
from flask import Flask, jsonify, render_template_string

# Configuração de encoding
if sys.version_info[0] >= 3:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Configurar Flask
app = Flask(__name__)
app.secret_key = 'encceja-test-2025'

# Configurar logging
logging.basicConfig(level=logging.INFO)

# Template HTML simples embutido
HOME_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Teste VPS</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .header { 
            background: #0066cc; 
            color: white; 
            padding: 30px; 
            text-align: center; 
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .status-box { 
            background: #d4edda; 
            border: 1px solid #c3e6cb; 
            padding: 20px; 
            border-radius: 5px;
            margin: 20px 0;
        }
        .test-links {
            background: white;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .test-links a {
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 5px;
            margin: 5px;
        }
        .info { background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>✅ ENCCEJA 2025</h1>
        <p>Sistema de Teste - VPS Funcionando</p>
    </div>
    
    <div class="status-box">
        <h3>🎯 Status do Sistema</h3>
        <p><strong>Status:</strong> ✅ Online e Funcionando</p>
        <p><strong>Servidor:</strong> Flask + Gunicorn</p>
        <p><strong>Ambiente:</strong> VPS Hostinger</p>
        <p><strong>Data/Hora:</strong> {{ timestamp }}</p>
    </div>
    
    <div class="test-links">
        <h3>🔧 Links de Teste</h3>
        <a href="/status">Status JSON</a>
        <a href="/test-cpf">Teste CPF</a>
        <a href="/inscricao-simples">Inscrição Simples</a>
        <a href="/health">Health Check</a>
    </div>
    
    <div class="info">
        <h3>📋 Próximos Passos</h3>
        <p>1. Se esta página está carregando, o servidor Flask está funcionando</p>
        <p>2. Teste os links acima para verificar as APIs</p>
        <p>3. Verifique os logs: <code>tail -f /var/log/encceja_output.log</code></p>
        <p>4. Depois de confirmar que tudo funciona, substitua por app.py principal</p>
    </div>
</body>
</html>
'''

INSCRICAO_TEMPLATE = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ENCCEJA 2025 - Inscrição Teste</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 600px; margin: 50px auto; padding: 20px; }
        .header { background: #0066cc; color: white; padding: 20px; text-align: center; }
        .form-group { margin: 15px 0; }
        input[type="text"] { width: 100%; padding: 10px; font-size: 16px; }
        button { background: #28a745; color: white; padding: 15px 30px; font-size: 16px; border: none; cursor: pointer; }
        .result { margin: 20px 0; padding: 20px; background: #f8f9fa; border: 1px solid #ddd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>ENCCEJA 2025</h1>
        <p>Formulário de Teste - Inscrição</p>
    </div>
    
    <h2>Consultar CPF (Teste)</h2>
    <form onsubmit="consultarCPF(event)">
        <div class="form-group">
            <label>Digite seu CPF:</label>
            <input type="text" id="cpfInput" placeholder="000.000.000-00" maxlength="14" required>
        </div>
        <button type="submit">Consultar CPF</button>
    </form>
    
    <div id="resultado" class="result" style="display: none;">
        <h3>Resultado do Teste</h3>
        <p id="resultadoTexto"></p>
    </div>
    
    <script>
    function consultarCPF(event) {
        event.preventDefault();
        
        const cpfInput = document.getElementById('cpfInput');
        const resultado = document.getElementById('resultado');
        const resultadoTexto = document.getElementById('resultadoTexto');
        
        const cpf = cpfInput.value.replace(/\\D/g, '');
        
        if (cpf.length !== 11) {
            alert('CPF deve ter 11 dígitos');
            return;
        }
        
        resultadoTexto.innerHTML = 'Consultando CPF: ' + cpf + '...<br>Aguarde...';
        resultado.style.display = 'block';
        
        fetch('/api/consultar-cpf-teste?cpf=' + cpf)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    resultadoTexto.innerHTML = 
                        '<strong>✅ CPF Processado com Sucesso!</strong><br>' +
                        'CPF: ' + data.cpf + '<br>' +
                        'Status: ' + data.status + '<br>' +
                        'Timestamp: ' + data.timestamp;
                } else {
                    resultadoTexto.innerHTML = '<strong>❌ Erro:</strong> ' + data.error;
                }
            })
            .catch(error => {
                resultadoTexto.innerHTML = '<strong>❌ Erro de Conexão:</strong> ' + error;
            });
    }
    </script>
</body>
</html>
'''

@app.route('/')
def home():
    """Página inicial de teste"""
    from datetime import datetime
    app.logger.info("VPS TEST: Acessando página inicial")
    return render_template_string(HOME_TEMPLATE, 
                                timestamp=datetime.now().strftime('%d/%m/%Y %H:%M:%S'))

@app.route('/status')
def status():
    """Status do sistema em JSON"""
    from datetime import datetime
    app.logger.info("VPS TEST: Consultando status")
    return jsonify({
        'status': 'online',
        'message': 'ENCCEJA 2025 - Sistema de teste funcionando',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0-test',
        'environment': 'VPS Hostinger'
    })

@app.route('/health')
def health():
    """Health check simples"""
    return "OK - ENCCEJA 2025 VPS Test", 200

@app.route('/inscricao-simples')
def inscricao_simples():
    """Página de inscrição de teste"""
    app.logger.info("VPS TEST: Renderizando inscrição de teste")
    return render_template_string(INSCRICAO_TEMPLATE)

@app.route('/api/consultar-cpf-teste')
def consultar_cpf_teste():
    """API de teste para consulta de CPF"""
    from datetime import datetime
    
    cpf = request.args.get('cpf', '').strip()
    app.logger.info(f"VPS TEST: Consultando CPF de teste: {cpf}")
    
    if not cpf:
        return jsonify({'success': False, 'error': 'CPF não fornecido'})
    
    # Limpar CPF
    cpf_clean = ''.join(filter(str.isdigit, cpf))
    
    if len(cpf_clean) != 11:
        return jsonify({'success': False, 'error': 'CPF deve ter 11 dígitos'})
    
    # Simular processamento (para teste)
    import time
    time.sleep(1)  # Simular delay de API
    
    # Retornar sucesso sempre (é só um teste)
    return jsonify({
        'success': True,
        'cpf': cpf_clean,
        'status': 'CPF processado com sucesso (TESTE)',
        'message': 'Esta é uma simulação para testar o ambiente VPS',
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    })

@app.route('/test-cpf')
def test_cpf_page():
    """Página de teste rápido de CPF"""
    return '''
    <h1>Teste Rápido de CPF</h1>
    <p><a href="/api/consultar-cpf-teste?cpf=12345678901">Teste CPF: 12345678901</a></p>
    <p><a href="/api/consultar-cpf-teste?cpf=98765432100">Teste CPF: 98765432100</a></p>
    <p><a href="/">← Voltar</a></p>
    '''

@app.errorhandler(404)
def not_found(error):
    return '''
    <h1>404 - Página não encontrada</h1>
    <p>A página que você procura não existe neste teste.</p>
    <p><a href="/">← Ir para página inicial</a></p>
    ''', 404

@app.errorhandler(500)
def internal_error(error):
    return '''
    <h1>500 - Erro interno</h1>
    <p>Houve um erro interno no servidor de teste.</p>
    <p><a href="/">← Ir para página inicial</a></p>
    ''', 500

if __name__ == '__main__':
    app.logger.info("=== ENCCEJA 2025 - APLICAÇÃO DE TESTE VPS ===")
    app.logger.info("Esta é uma versão simplificada para testar o ambiente")
    app.logger.info("Iniciando na porta 5000...")
    app.run(host='0.0.0.0', port=5000, debug=True)