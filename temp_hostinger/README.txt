ENCCEJA PIX Payment System - Deploy Hostinger
=============================================

INSTALAÇÃO RÁPIDA:
1. Extrair este ZIP na pasta public_html da Hostinger
2. Via terminal SSH ou painel Python: pip install -r requirements.txt  
3. Executar: python main.py
4. Testar: https://seudominio.com

ESTRUTURA DE ARQUIVOS:
- app.py (aplicação Flask principal)
- main.py (ponto de entrada)
- witepay_gateway.py (gateway PIX WitePay)
- requirements.txt (dependências Python)
- .env (configurações com chaves funcionais)
- static/css/ (CSS compilado Tailwind)
- static/fonts/ (fontes CAIXA e Rawline)
- templates/ (21 páginas HTML)

CHAVES JÁ CONFIGURADAS:
✓ WITEPAY_API_KEY: wtp_7819b0bb469f4b52a96feca4ddc46ba4
✓ SESSION_SECRET: configurada
✓ GOOGLE_PIXEL_ID: 6859ccee5af20eab22a408ef
✓ FACEBOOK_PIXELS: 3 pixels ativos

SISTEMA FUNCIONAL:
- Pagamentos PIX R$ 93,40
- Tracking conversões Google/Facebook
- Interface ENCCEJA oficial
- Webhook WitePay configurado

URLS PARA TESTAR:
- / (página inicial)
- /pagamento (gerar PIX)
- /verificar-pagamento (status)
- /witepay-postback (webhook)

Tudo pronto para produção!