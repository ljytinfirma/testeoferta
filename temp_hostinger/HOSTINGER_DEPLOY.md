# Hostinger Deployment Guide

## Pré-requisitos na Hostinger

1. **Python 3.8+** (verificar se está disponível)
2. **Node.js 16+** (para build dos assets)
3. **Variáveis de ambiente** configuradas no painel

## Estrutura do Projeto

```
projeto/
├── app.py                 # Aplicação Flask principal
├── main.py               # Ponto de entrada
├── requirements.txt      # Dependências Python
├── package.json         # Dependências Node.js
├── tailwind.config.js   # Configuração Tailwind
├── postcss.config.js    # Configuração PostCSS
├── static/
│   ├── css/
│   │   ├── input.css    # CSS source
│   │   └── output.css   # CSS compilado (gerado)
│   └── fonts/           # Fontes CAIXA (copiadas)
├── templates/           # Templates Jinja2
└── attached_assets/     # Assets originais
```

## Passos para Deploy na Hostinger

### 1. Preparar o Ambiente Local

```bash
# Instalar dependências NPM
npm install

# Gerar CSS compilado
npm run build
```

### 2. Variáveis de Ambiente Obrigatórias

Configure no painel da Hostinger:

```env
# WitePay API
WITEPAY_API_KEY=sua_chave_witepay_aqui

# Flask
SESSION_SECRET=sua_chave_secreta_session_aqui
FLASK_ENV=production

# Database (se usar PostgreSQL)
DATABASE_URL=postgresql://user:pass@localhost/dbname

# Opcional - Configurações SMS
SMSDEV_TOKEN=seu_token_smsdev
OWEN_TOKEN=seu_token_owen
```

### 3. Estrutura de Arquivos para Upload

**Arquivos essenciais para enviar:**
- `app.py` - Aplicação principal
- `main.py` - Entrada da aplicação
- `requirements.txt` - Dependências Python
- `witepay_gateway.py` - Gateway de pagamento
- `templates/` - Todos os templates HTML
- `static/css/output.css` - CSS compilado (gerado pelo build)
- `static/fonts/` - Fontes CAIXA (copiadas do build)

**Não enviar:**
- `node_modules/` - Dependências NPM
- `attached_assets/` - Assets originais
- `static/css/input.css` - CSS source
- Arquivos de configuração Node.js

### 4. Comandos na Hostinger

```bash
# Instalar dependências Python
pip install -r requirements.txt

# Iniciar aplicação
python main.py
# ou
gunicorn --bind 0.0.0.0:5000 main:app
```

### 5. Configuração do Servidor Web

**Para Apache (.htaccess):**
```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ main.py/$1 [QSA,L]
```

**Para Nginx:**
```nginx
location / {
    proxy_pass http://127.0.0.1:5000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

## Funcionalidades Principais

### Sistema de Pagamentos PIX
- **WitePay Integration**: R$ 93,40 por inscrição
- **QR Code Generation**: PIX codes for mobile payments
- **Postback Validation**: Real-time payment confirmations

### Tracking e Analytics
- **UTMFY Google Pixel**: ID 6859ccee5af20eab22a408ef
- **Conversion Events**: Triggered on confirmed payments
- **Session Management**: Payment status validation

### Recursos de Segurança
- **Domain Restrictions**: Referrer-based access control
- **Device Detection**: Mobile-only access
- **Bot Protection**: User agent validation

## Monitoramento

### Logs Importantes
```python
# Payment tracking
INFO:app:[WITEPAY] Payment created: ch_xxxxx
INFO:app:[UTMFY_GOOGLE_PIXEL] Conversion triggered

# Security events
INFO:app:[PROD] Access allowed for route
INFO:app:[DOMAIN_CHECK] Referrer validation
```

### Endpoints de Status
- `/` - Página inicial
- `/pagamento` - Geração de pagamentos PIX
- `/verificar-pagamento` - Status do pagamento
- `/witepay-postback` - Webhook do WitePay

## Troubleshooting

### Erro: CSS não carrega
```bash
npm run build:css
```

### Erro: Fontes não aparecem
```bash
npm run copy:assets
```

### Erro: Pagamentos não funcionam
- Verificar WITEPAY_API_KEY
- Checar logs do endpoint /witepay-postback
- Validar formato do CPF no frontend

### Performance
- CSS minificado via Tailwind
- Fontes com font-display: swap
- Lazy loading de assets não críticos