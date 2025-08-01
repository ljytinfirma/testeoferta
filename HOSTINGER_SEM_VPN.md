# Como Hospedar na Hostinger SEM VPN

## 🌐 Métodos de Upload sem VPN

### **Método 1: File Manager Web (Recomendado)**
1. **Acesse o painel Hostinger** via navegador
2. **Vá em "File Manager"** no menu lateral
3. **Navegue até public_html** (pasta do seu site)
4. **Upload do arquivo TAR.GZ**:
   - Clique em "Upload"
   - Selecione `encceja-hostinger-CORRIGIDO.tar.gz`
   - Aguarde o upload (710KB - alguns segundos)
5. **Extrair arquivo**:
   - Clique com botão direito no arquivo TAR.GZ
   - Selecione "Extract" ou "Descompactar"
   - Confirme a extração

### **Método 2: FTP via Navegador (FileZilla Online)**
1. **Use cliente FTP web** como:
   - net2ftp.com
   - ftpmanager.org
   - Ou qualquer cliente FTP online
2. **Conecte com dados Hostinger**:
   - Host: ftp.seudominio.com
   - Usuário: seu_usuario_ftp
   - Senha: sua_senha_ftp
3. **Upload dos arquivos** diretamente

### **Método 3: Upload Individual (Mais Lento)**
Se o arquivo TAR.GZ for muito grande:

1. **Extraia o arquivo** no seu computador
2. **Upload individual** via File Manager:
   - `app.py`
   - `main.py`
   - `witepay_gateway.py`
   - `requirements.txt`
   - Pasta `static/` completa
   - Pasta `templates/` completa

## ⚙️ Configuração no Servidor Hostinger

### **1. Terminal SSH (se disponível)**
```bash
# Navegar até a pasta do projeto
cd public_html

# Instalar dependências Python
pip install -r requirements.txt

# Verificar instalação
python3 --version
pip --version
```

### **2. Configurar Variáveis de Ambiente**
Criar arquivo `.env` via File Manager:
```env
WITEPAY_API_KEY=sua_chave_witepay_aqui
SESSION_SECRET=uma_chave_aleatoria_de_32_caracteres
FLASK_ENV=production
```

### **3. Configurar Python/WSGI**
Na Hostinger, você precisa:

**Opção A - Python App (se suportado):**
1. Vá em "Python App" no painel
2. Crie nova aplicação Python
3. Configure startup file: `main.py`
4. Define application object: `app`

**Opção B - Subdomínio Python:**
1. Crie subdomínio (ex: app.seusite.com)
2. Configure para apontar para pasta do projeto
3. Adicione arquivo `.htaccess`:

```apache
RewriteEngine On
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ main.py/$1 [QSA,L]

# Python CGI
AddHandler cgi-script .py
Options +ExecCGI
```

## 🚀 Testar a Aplicação

### **Verificações Importantes:**

1. **Teste URL:** `https://seudominio.com/app`
2. **Verifique logs:** Painel Hostinger → Error Logs
3. **Teste pagamento:** Acesse `/pagamento` e teste PIX

### **URLs Importantes para Testar:**
- `/` - Página inicial
- `/pagamento` - Gerar PIX
- `/verificar-pagamento` - Status
- `/witepay-postback` - Webhook (para WitePay)

## 🔧 Troubleshooting Comum

### **Erro: Python não encontrado**
```bash
# No terminal SSH ou adicionar no .htaccess
#!/usr/bin/python3
```

### **Erro: Módulos não encontrados**
```bash
# Instalar dependências no diretório correto
pip3 install --user -r requirements.txt
```

### **Erro: Permissões**
```bash
# Via File Manager, definir permissões:
# Arquivos Python: 755
# Arquivos estáticos: 644
chmod 755 *.py
chmod 644 static/css/*.css
```

## 📋 Checklist Final

- [ ] Arquivo extraído em public_html
- [ ] Dependências Python instaladas
- [ ] Arquivo .env configurado
- [ ] WITEPAY_API_KEY definida
- [ ] Permissões corretas (755 para .py)
- [ ] Teste das páginas principais
- [ ] Logs verificados (sem erros)

## 💡 Dicas Importantes

1. **Use HTTPS:** Sempre configure SSL/TLS
2. **Backup:** Faça backup antes de mudanças
3. **Logs:** Monitore Error Logs regularmente
4. **Performance:** Hostinger suporta Python mas pode ser limitado
5. **Domínio:** Configure DNS corretamente

## 🆘 Se Não Funcionar

**Alternativas:**
1. **Vercel** (grátis, fácil deploy Python)
2. **Railway** (suporte Flask nativo)
3. **PythonAnywhere** (especializado em Python)
4. **Heroku** (mais caro, mas confiável)

Todas essas opções funcionam sem VPN e têm deploy mais simples que Hostinger tradicional.