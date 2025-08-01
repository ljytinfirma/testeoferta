# Upload do Projeto ENCCEJA Real para o VPS

## Situação Atual
✅ Python funcionando no VPS
✅ Supervisor e Nginx configurados  
❌ Projeto atual é apenas um teste básico
🎯 Objetivo: Fazer upload do projeto ENCCEJA completo

## Método 1: Upload via MobaXterm (Recomendado)

### Passo 1: Preparar arquivos localmente
No seu computador:
1. Baixe todos os arquivos do projeto do Replit
2. Crie uma pasta com os arquivos principais:
   ```
   encceja-projeto/
   ├── app.py
   ├── main.py  
   ├── witepay_gateway.py
   ├── templates/
   │   ├── index.html
   │   ├── encceja_info.html
   │   ├── pagamento.html
   │   └── (outros templates)
   ├── static/
   │   ├── css/output.css
   │   └── fonts/
   └── requirements.txt
   ```

### Passo 2: Backup da configuração atual
No terminal do VPS:
```bash
cd /var/www/encceja
mv app_simples.py app_simples_backup.py
```

### Passo 3: Upload via MobaXterm
1. **MobaXterm** → Conectar no VPS
2. **Painel esquerdo** (local) → Navegar até pasta encceja-projeto
3. **Painel direito** (VPS) → Navegar até /var/www/encceja
4. **Selecionar todos os arquivos** do projeto local
5. **Arrastar** para o VPS (sobrescrever quando perguntar)

### Passo 4: Configurar .env com chaves reais
```bash
cd /var/www/encceja
nano .env
```

**Conteúdo:**
```env
SESSION_SECRET=encceja_secret_key_2025_production
WITEPAY_API_KEY=wtp_7819b0bb469f4b52a96feca4ddc46ba4
DOMAIN_RESTRICTION_ENABLED=false
FLASK_ENV=production
GOOGLE_PIXEL_ID=6859ccee5af20eab22a408ef
```

### Passo 5: Instalar dependências do projeto real
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Passo 6: Atualizar configuração do Supervisor
```bash
sudo nano /etc/supervisor/conf.d/encceja.conf
```

**Conteúdo:**
```ini
[program:encceja]
command=/var/www/encceja/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 2 main:app
directory=/var/www/encceja
user=root
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/encceja.log
stderr_logfile=/var/log/encceja_error.log
environment=PATH="/var/www/encceja/venv/bin"
```

### Passo 7: Reiniciar aplicação
```bash
sudo supervisorctl restart encceja
sudo supervisorctl status
```

## Método 2: Download direto do Replit (Alternativo)

### Se você não conseguir fazer upload via MobaXterm:
```bash
# No VPS, fazer backup e limpar
cd /var/www/encceja
mv * backup/

# Baixar projeto do Replit (se estiver no GitHub)
git clone https://github.com/seu-usuario/projeto-encceja.git .

# Ou criar arquivo por arquivo (trabalhoso)
```

## Método 3: Recriar projeto arquivo por arquivo

### Se precisar recriar manualmente, começar com:
```bash
cd /var/www/encceja
nano app.py
```

**Copiar conteúdo do app.py original do Replit**

```bash
nano main.py
```

**Copiar conteúdo do main.py original**

### Criar estrutura de pastas:
```bash
mkdir -p templates static/css static/fonts
```

## Verificação Final

### Após upload, testar:
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Testar aplicação
python main.py

# Se funcionar, parar e usar supervisor
# Ctrl+C

# Reiniciar supervisor
sudo supervisorctl restart encceja

# Verificar logs
tail -f /var/log/encceja.log

# Testar acesso
curl http://localhost:5000
```

## Estrutura Final Esperada

```
/var/www/encceja/
├── venv/                    # Ambiente virtual
├── app.py                   # Aplicação Flask principal
├── main.py                  # Ponto de entrada
├── witepay_gateway.py       # Gateway de pagamento
├── .env                     # Variáveis de ambiente
├── requirements.txt         # Dependências
├── templates/
│   ├── index.html          # Página inicial CPF
│   ├── encceja_info.html   # Dados encontrados
│   ├── pagamento.html      # Pagamento PIX
│   ├── validar_dados.html  # Confirmar dados
│   └── shared_resources.html
└── static/
    ├── css/output.css      # Estilos Tailwind
    └── fonts/              # Fontes CAIXA
```

## URLs do Funil Funcionais

Após upload correto:
- `/` - Consulta CPF
- `/encceja-info` - Dados encontrados  
- `/validar-dados` - Confirmar dados
- `/pagamento` - Gerar PIX R$ 93,40

Execute o Método 1 fazendo upload dos arquivos reais via MobaXterm!