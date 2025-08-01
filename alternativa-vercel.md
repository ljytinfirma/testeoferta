# Alternativa MAIS FÁCIL: Deploy no Vercel

Se a Hostinger for complicada, o **Vercel** é muito mais simples:

## 🚀 Deploy no Vercel (5 minutos)

### **1. Preparar Projeto**
Adicionar arquivo `vercel.json`:
```json
{
  "version": 2,
  "builds": [
    {
      "src": "main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "main.py"
    }
  ],
  "env": {
    "WITEPAY_API_KEY": "@witepay-api-key",
    "SESSION_SECRET": "@session-secret"
  }
}
```

### **2. Deploy**
```bash
# Instalar Vercel CLI
npm install -g vercel

# Fazer login
vercel login

# Deploy
vercel --prod
```

### **3. Configurar Variáveis**
```bash
vercel env add WITEPAY_API_KEY
vercel env add SESSION_SECRET
```

**Pronto!** Seu site estará em: `https://seu-projeto.vercel.app`

## ✅ Vantagens do Vercel
- Deploy automático via Git
- SSL gratuito
- CDN global
- Sem configuração de servidor
- Logs em tempo real
- Zero downtime

Quer que eu prepare o projeto para Vercel também?