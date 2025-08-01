#!/usr/bin/env python3
"""
VPS - Teste mínimo para verificar se Python/Flask funciona
Upload como test.py na VPS e execute: python3 test.py
"""

print("🔍 TESTE VPS - Verificando ambiente...")

# Teste 1: Python básico
try:
    import sys
    print(f"✅ Python {sys.version}")
except Exception as e:
    print(f"❌ Python erro: {e}")
    exit(1)

# Teste 2: Flask
try:
    import flask
    print(f"✅ Flask {flask.__version__}")
except Exception as e:
    print(f"❌ Flask não encontrado: {e}")
    print("💡 Instale: pip install flask")
    exit(1)

# Teste 3: Aplicação mínima
try:
    from flask import Flask
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return """
        <h1>✅ VPS FUNCIONANDO!</h1>
        <p>Python: OK</p>
        <p>Flask: OK</p>
        <p>Aplicação: Rodando</p>
        <hr>
        <small>ENCCEJA VPS Test - Success</small>
        """
    
    print("🌐 Iniciando servidor na porta 5000...")
    print("🔗 Acesse: http://seu-dominio.com")
    print("⏹️  Para parar: Ctrl+C")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
    
except Exception as e:
    print(f"❌ Erro ao iniciar Flask: {e}")
    exit(1)