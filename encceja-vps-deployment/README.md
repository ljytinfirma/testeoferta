# 🚀 ENCCEJA WITEPAY - DEPLOYMENT VPS

## Arquivos Inclusos

- `app.py` - Aplicação Flask principal
- `templates/` - Templates HTML do sistema
- `static/` - Arquivos CSS, JS, imagens e fontes
- `vps_requirements.txt` - Dependências Python
- `deploy_vps.sh` - Script automático de instalação
- `VPS_UBUNTU_DEPLOYMENT_GUIDE.md` - Guia completo
- `DEPLOYMENT_INSTRUCTIONS.md` - Instruções rápidas

## 🎯 INSTALAÇÃO RÁPIDA

1. **Conecte ao VPS:**
```bash
ssh root@SEU_IP_VPS
```

2. **Faça upload desta pasta para o VPS**

3. **Execute o script de instalação:**
```bash
cd encceja-vps-deployment
bash deploy_vps.sh
```

4. **Copie os arquivos do projeto:**
```bash
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/

# Reinicie a aplicação
supervisorctl restart encceja
```

## ✅ VERIFICAÇÃO

Teste se está funcionando:
```bash
curl -I http://localhost:5000
# Deve retornar: HTTP/1.1 200 OK
```

Ver logs:
```bash
tail -f /var/log/encceja.log
```

## 🌐 ACESSO

Depois da instalação, acesse:
`http://SEU_IP_VPS`

**Sistema funcionando com:**
- CPF API real
- WitePay PIX R$ 93,40
- QR Code funcional
- Funil completo preservado