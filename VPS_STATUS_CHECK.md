# VPS - Verificacao de Status ENCCEJA

## Status Atual: BACKOFF (Exited too quickly)

O erro indica que a aplicacao esta falhando ao iniciar. Vamos diagnosticar:

## 1. Verificar Logs Detalhados

```bash
# Ver logs completos
tail -f /var/log/encceja.log

# Ver logs do Supervisor
supervisorctl tail -f encceja

# Verificar erro especifico
cat /var/log/encceja.log | grep ERROR
```

## 2. Testar Aplicacao Manual

```bash
cd /var/www/encceja
source venv/bin/activate

# Testar se Python funciona
python --version

# Testar imports
python -c "import flask; print('Flask OK')"
python -c "import requests; print('Requests OK')"

# Testar aplicacao
python app.py
```

## 3. Verificar Estrutura de Arquivos

```bash
ls -la /var/www/encceja/
ls -la /var/www/encceja/templates/
ls -la /var/www/encceja/static/
```

## 4. Corrigir Encoding UTF-8

```bash
# Verificar se arquivo tem problemas de encoding
file /var/www/encceja/app.py

# Se necessario, recriar arquivo
cp /var/www/encceja/app.py /var/www/encceja/app_backup.py
```

## 5. Usar Versao Limpa

Use o arquivo `VPS_FINAL_DEPLOYMENT_COMPLETE.py` que:
- Remove caracteres UTF-8 problematicos
- Adiciona tratamento de encoding
- Inclui fallbacks para templates
- Logs mais detalhados

```bash
# Upload do novo arquivo
# VPS_FINAL_DEPLOYMENT_COMPLETE.py -> /var/www/encceja/app.py

# Reiniciar
supervisorctl restart encceja
supervisorctl status encceja
```

## 6. Teste Minimo

Se ainda falhar, criar teste minimo:

```bash
cat > /var/www/encceja/test_minimal.py << 'EOF'
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "ENCCEJA VPS Funcionando!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

python test_minimal.py
```

## 7. Diagnostico Completo

Execute este script de diagnostico:

```bash
echo "=== DIAGNOSTICO ENCCEJA VPS ==="
echo "Data: $(date)"
echo "Python: $(python --version)"
echo "Flask: $(python -c 'import flask; print(flask.__version__)' 2>/dev/null || echo 'NAO INSTALADO')"
echo "Supervisor: $(supervisorctl status encceja)"
echo "Arquivos:"
ls -la /var/www/encceja/app.py
echo "Logs recentes:"
tail -5 /var/log/encceja.log
echo "Teste import:"
cd /var/www/encceja && source venv/bin/activate && python -c "import app; print('Import OK')" 2>&1 || echo "Import FALHOU"
```

O erro mais provavel e:
1. **Encoding UTF-8** no arquivo Python
2. **Template faltando** (inscricao.html)
3. **Import falhando** (witepay_gateway.py)

Use o `VPS_FINAL_DEPLOYMENT_COMPLETE.py` que resolve esses problemas.