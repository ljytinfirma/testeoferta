# Como Corrigir o Erro "Missing script: build"

## 🔧 Problema
O package.json extraído não contém os scripts de build necessários.

## ✅ Solução

### 1. Substituir o package.json
**Substitua** o arquivo `package.json` pelo conteúdo correto:

```json
{
  "name": "encceja-pix-payment-system",
  "version": "1.0.0",
  "description": "Brazilian PIX Payment System for ENCCEJA 2025 exam enrollment with WitePay integration",
  "main": "app.py",
  "scripts": {
    "build": "echo Building static assets... && npm run build:css && npm run copy:assets",
    "build:css": "npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify",
    "copy:assets": "mkdir -p static/fonts && cp attached_assets/CAIXAStd-*.woff static/fonts/ 2>/dev/null || echo No font files to copy",
    "dev": "python main.py",
    "start": "gunicorn --bind 0.0.0.0:5000 --reuse-port main:app",
    "postinstall": "pip install -r requirements.txt"
  },
  "keywords": ["pix", "payment", "encceja", "brazil", "education", "flask", "witepay"],
  "author": "ENCCEJA Payment System",
  "license": "MIT",
  "engines": {
    "node": ">=16.0.0",
    "python": ">=3.8.0"
  },
  "dependencies": {
    "@tailwindcss/forms": "^0.5.10",
    "autoprefixer": "^10.4.21",
    "postcss": "^8.5.6",
    "tailwindcss": "^3.4.0"
  }
}
```

### 2. Comandos na Ordem Correta

```bash
# 1. Instalar dependências NPM
npm install

# 2. Executar o build
npm run build

# 3. Instalar dependências Python
pip install -r requirements.txt

# 4. Rodar a aplicação
python main.py
```

## 📁 Arquivos Necessários

Certifique-se de que você tem estes arquivos:
- `package.json` (com os scripts corretos)
- `tailwind.config.js`
- `postcss.config.js`
- `static/css/input.css`
- `attached_assets/CAIXAStd-*.woff` (fontes)

## 🔍 Se Ainda Der Erro

**Alternativa - Build Manual:**
```bash
# Criar CSS manualmente
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Copiar fontes manualmente
mkdir -p static/fonts
cp attached_assets/CAIXAStd-*.woff static/fonts/
```

## 💡 Versão Simplificada (Se NPM não funcionar)

O CSS já está compilado no arquivo `static/css/output.css` no pacote. Você pode:

1. **Pular o npm build** completamente
2. **Usar apenas Python:**
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

O sistema já tem o CSS compilado e pronto para usar!