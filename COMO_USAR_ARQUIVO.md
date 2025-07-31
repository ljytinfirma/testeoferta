# Como Usar o Arquivo TAR.GZ na Hostinger

## 📁 Arquivo Criado
**Nome:** `encceja-hostinger-ready.tar.gz`  
**Tamanho:** 709 KB  
**Arquivos:** 41 total

## 🔧 Como Extrair e Usar

### 1. Download do Arquivo
- Baixe o arquivo `encceja-hostinger-ready.tar.gz` do Replit
- Salve em seu computador

### 2. Extrair no Computador (Opcional)
```bash
# Windows (usando WSL ou Git Bash)
tar -xzf encceja-hostinger-ready.tar.gz

# Linux/Mac
tar -xzf encceja-hostinger-ready.tar.gz
```

### 3. Upload na Hostinger
**Opção A - Upload do TAR.GZ:**
1. Acesse o File Manager da Hostinger
2. Navegue até a pasta do seu domínio (public_html)
3. Upload do arquivo `encceja-hostinger-ready.tar.gz`
4. Clique com botão direito → "Extract"

**Opção B - Upload Individual:**
1. Extraia o arquivo no seu computador
2. Upload apenas dos arquivos principais:
   - `app.py`
   - `main.py` 
   - `witepay_gateway.py`
   - `requirements.txt`
   - Pasta `static/` completa
   - Pasta `templates/` completa

## 🚀 Configuração na Hostinger

### 1. Instalar Dependências Python
```bash
# Terminal SSH da Hostinger
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
Criar arquivo `.env` com:
```env
WITEPAY_API_KEY=sua_chave_witepay_aqui
SESSION_SECRET=sua_chave_secreta_sessao_aqui
FLASK_ENV=production
```

### 3. Testar NPM Build (Opcional)
```bash
npm install
npm run build
```

### 4. Iniciar Aplicação
```bash
python main.py
```

## 📋 Estrutura dos Arquivos

```
encceja-project/
├── app.py                     # Aplicação Flask principal
├── main.py                    # Ponto de entrada
├── witepay_gateway.py         # Gateway PIX WitePay
├── requirements.txt           # Dependências Python
├── static/
│   ├── css/output.css        # CSS compilado (8.9KB)
│   └── fonts/                # Fontes CAIXA + Rawline
├── templates/                # 21 páginas HTML
├── package.json              # Configuração NPM
├── tailwind.config.js        # Configuração Tailwind
├── HOSTINGER_DEPLOY.md       # Guia completo
└── .env.example             # Exemplo de variáveis
```

## ✅ Funcionalidades Incluídas

- **Pagamentos PIX:** WitePay integration (R$ 93,40)
- **Tracking:** UTMFY Google Pixel (ID: 6859ccee5af20eab22a408ef)
- **Design:** Responsivo com Tailwind CSS
- **Branding:** ENCCEJA 2025 oficial
- **Segurança:** Validação de domínio e sessões

## 🔍 Troubleshooting

**CSS não carrega:**
- Verificar se `static/css/output.css` foi carregado
- Rodar `npm run build` se necessário

**Pagamentos não funcionam:**
- Configurar `WITEPAY_API_KEY` no arquivo `.env`
- Verificar logs em `/witepay-postback`

**Fontes não aparecem:**
- Verificar se pasta `static/fonts/` tem as fontes CAIXA
- Executar `npm run copy:assets`

## 📞 Suporte
Consulte o arquivo `HOSTINGER_DEPLOY.md` para instruções detalhadas ou `build-status.txt` para status do build.