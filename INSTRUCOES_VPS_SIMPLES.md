# 📋 INSTRUÇÕES SIMPLES - VPS HOSTINGER

## 🎯 O QUE VOCÊ PRECISA FAZER:

### 1. BAIXAR O ARQUIVO
Baixe: `encceja-vps-deployment.tar.gz` (50MB)

### 2. CONECTAR AO VPS
```bash
ssh root@SEU_IP_VPS
```

### 3. FAZER UPLOAD
Opção A - SCP:
```bash
scp encceja-vps-deployment.tar.gz root@SEU_IP_VPS:/root/
```

Opção B - File Manager Hostinger (mais fácil):
- Entre no painel Hostinger
- Vá em File Manager
- Faça upload do arquivo

### 4. EXTRAIR NO VPS
```bash
cd /root
tar -xzf encceja-vps-deployment.tar.gz
cd encceja-vps-deployment
```

### 5. INSTALAR AUTOMATICAMENTE
```bash
chmod +x deploy_vps.sh
bash deploy_vps.sh
```

### 6. COPIAR ARQUIVOS
```bash
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/
chown -R www-data:www-data /var/www/encceja
supervisorctl restart encceja
```

### 7. TESTAR
```bash
curl -I http://localhost:5000
```
Deve retornar: `HTTP/1.1 200 OK`

## ✅ PRONTO!
Acesse: `http://SEU_IP_VPS`

**Sistema funcionando com PIX WitePay R$ 93,40** 🎉