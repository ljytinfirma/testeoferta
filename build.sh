#!/bin/bash

echo "🚀 Building ENCCEJA PIX Payment System for Hostinger..."

# Criar diretórios necessários
echo "📁 Creating directories..."
mkdir -p static/css
mkdir -p static/fonts
mkdir -p static/js

# Instalar dependências NPM se não existirem
if [ ! -d "node_modules" ]; then
    echo "📦 Installing NPM dependencies..."
    npm install
fi

# Copiar arquivos de configuração para package.json correto
echo "⚙️ Setting up build configuration..."
if [ -f "hostinger-config.json" ]; then
    cp package.json package-original.json
    cp hostinger-config.json package.json
fi

# Build CSS com Tailwind
echo "🎨 Building CSS with Tailwind..."
npx tailwindcss -i ./static/css/input.css -o ./static/css/output.css --minify

# Copiar fontes CAIXA
echo "🔤 Copying CAIXA fonts..."
if ls attached_assets/CAIXAStd-*.woff 1> /dev/null 2>&1; then
    cp attached_assets/CAIXAStd-*.woff static/fonts/
    echo "✅ Fonts copied successfully"
else
    echo "⚠️ No CAIXA font files found in attached_assets/"
fi

# Restaurar package.json original
if [ -f "package-original.json" ]; then
    mv package-original.json package.json
fi

# Criar arquivo de status
echo "📋 Creating build status..."
cat > build-status.txt << EOL
Build completed at: $(date)
CSS compiled: static/css/output.css
Fonts copied: $(ls static/fonts/ 2>/dev/null | wc -l) files
Node modules: $([ -d "node_modules" ] && echo "Present" || echo "Missing")
EOL

echo "✅ Build completed successfully!"
echo ""
echo "📦 Ready for Hostinger deployment:"
echo "   • CSS compiled to static/css/output.css"
echo "   • Fonts copied to static/fonts/"
echo "   • Use Python requirements.txt for server-side dependencies"
echo ""
echo "🔗 Next steps:"
echo "   1. Upload project files to Hostinger"
echo "   2. Configure environment variables (WITEPAY_API_KEY, SESSION_SECRET)"
echo "   3. Install Python dependencies: pip install -r requirements.txt"
echo "   4. Start application: python main.py"