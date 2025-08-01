# 🖥️ COMANDOS PARA VPS HOSTINGER - UBUNTU

## 1. CONECTAR AO VPS

### Via SSH (Terminal):
```bash
ssh root@SEU_IP_VPS
```

### Via Painel Hostinger:
- Acesse o painel da Hostinger
- Vá em VPS → Seu VPS → Terminal

## 2. FAZER UPLOAD DO PROJETO

### Método 1 - SCP (do seu computador):
```bash
scp encceja-vps-deployment.tar.gz root@SEU_IP_VPS:/root/
```

### Método 2 - File Manager Hostinger:
1. Acesse File Manager no painel
2. Faça upload do arquivo `encceja-vps-deployment.tar.gz`
3. Extraia o arquivo

### Método 3 - Terminal direto:
```bash
cd /root
wget "LINK_DO_ARQUIVO_AQUI"
```

## 3. EXTRAIR E INSTALAR

```bash
# Extrair arquivos
cd /root
tar -xzf encceja-vps-deployment.tar.gz
cd encceja-vps-deployment

# Dar permissão ao script
chmod +x deploy_vps.sh

# Executar instalação automática
bash deploy_vps.sh
```

## 4. COPIAR ARQUIVOS DO PROJETO

```bash
# Copiar arquivos principais
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/

# Definir permissões corretas
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja

# Reiniciar aplicação
supervisorctl restart encceja
```

## 5. VERIFICAR SE FUNCIONOU

```bash
# Testar conexão local
curl -I http://localhost:5000

# Ver logs em tempo real
tail -f /var/log/encceja.log

# Status dos serviços
supervisorctl status encceja
systemctl status nginx
```

## 6. ACESSAR O SISTEMA

No navegador, acesse:
- `http://SEU_IP_VPS`
- `http://seu-dominio.com` (se tiver domínio)

## 🔧 COMANDOS ÚTEIS

### Reiniciar serviços:
```bash
supervisorctl restart encceja
systemctl restart nginx
```

### Ver logs de erro:
```bash
tail -n 50 /var/log/encceja.log
tail -n 50 /var/log/nginx/error.log
```

### Verificar portas abertas:
```bash
netstat -tlnp | grep :5000
netstat -tlnp | grep :80
```

### Atualizar projeto (após mudanças):
```bash
cd /var/www/encceja
# Substituir arquivos atualizados
supervisorctl restart encceja
```

## 🚨 SOLUÇÃO DE PROBLEMAS

### App não inicia:
```bash
cd /var/www/encceja
source venv/bin/activate
python app.py
# Ver erros diretamente
```

### Nginx 502 Error:
```bash
supervisorctl status encceja
# Se parado: supervisorctl start encceja
```

### Permissões:
```bash
chown -R www-data:www-data /var/www/encceja
chmod -R 755 /var/www/encceja
```

**Pronto! Sistema funcionando na VPS Ubuntu Hostinger** 🎉