# VERSÃO CORRIGIDA PARA VPS - READY TO DEPLOY
# Arquivo app.py com as correções aplicadas

# [INCLUIR TODO O CONTEÚDO DO app.py ATUAL, MAS COM AS DUAS CORREÇÕES]

# Correção 1: Linha ~1698 - WitePay API Key
# ANTES:
# api_key = os.environ.get('WITEPAY_API_KEY')
# if not api_key:
#     app.logger.error("WITEPAY_API_KEY não encontrada")
#     return jsonify({'success': False, 'error': 'API key não configurada'}), 400

# DEPOIS:
# Usar chave WitePay fornecida pelo usuário (credenciais testadas)
api_key = "sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d"
app.logger.info("Usando chave WitePay fornecida pelo usuário")

# Correção 2: Linha ~1877 - API CPF
# ANTES:
# # Usar a API principal do projeto
# url = f"https://zincioinscricaositepdtedaferramenta.site/pagamento/{cpf_numerico}"

# DEPOIS:
# API principal está fora do ar, usar API alternativa funcionando
token = "1285fe4s-e931-4071-a848-3fac8273c55a"
url = f"https://consulta.fontesderenda.blog/cpf.php?token={token}&cpf={cpf_numerico}"

# NOTA: O arquivo completo seria muito grande para exibir aqui.
# Use o arquivo app.py atual e aplique apenas estas duas correções específicas.