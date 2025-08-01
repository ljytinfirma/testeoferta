#!/bin/bash
# VPS - Comandos rápidos para configurar projeto completo ENCCEJA

echo "🚀 Configurando ENCCEJA completo na VPS..."

# 1. Parar aplicação atual
supervisorctl stop encceja

# 2. Fazer backup do app atual
cp /var/www/encceja/app.py /var/www/encceja/app_backup.py

# 3. Ativar ambiente virtual
cd /var/www/encceja
source venv/bin/activate

# 4. Instalar dependências adicionais
pip install python-dotenv pillow qrcode[pil]

# 5. Criar arquivo .env com APIs reais
cat > .env << 'EOF'
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
SESSION_SECRET=encceja-vps-2025-secret-key
DOMAIN_RESTRICTION=false
CPF_API_TOKEN=1285fe4s-e931-4071-a848-3fac8273c55a
EOF

# 6. Adicionar carregamento do .env no app.py (se não existir)
if ! grep -q "load_dotenv" app.py; then
    sed -i '1i from dotenv import load_dotenv\nload_dotenv()\n' app.py
fi

# 7. Verificar estrutura de arquivos
echo "📁 Estrutura atual:"
ls -la /var/www/encceja/

# 8. Testar aplicação
echo "🧪 Testando aplicação..."
timeout 5 python app.py &
sleep 2

# 9. Reiniciar supervisor
supervisorctl start encceja
supervisorctl status encceja

# 10. Testar APIs
echo "🔍 Testando CPF API..."
curl -X POST http://127.0.0.1:5000/buscar-cpf \
  -H "Content-Type: application/json" \
  -d '{"cpf":"12345678901"}' 2>/dev/null | head -c 100

echo -e "\n🔍 Testando PIX..."
curl -X POST http://127.0.0.1:5000/criar-pagamento-pix \
  -H "Content-Type: application/json" \
  -d '{}' 2>/dev/null | head -c 100

echo -e "\n✅ Setup completo!"
echo "🌐 Acesse seu domínio para testar"
echo "📊 Status: $(supervisorctl status encceja | awk '{print $2}')"