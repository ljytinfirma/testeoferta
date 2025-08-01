# Hostinger: Python não encontrado - Soluções

## ❌ Problema
Hospedagem compartilhada Hostinger não tem Python instalado por padrão.

## ✅ Soluções Alternativas

### **Opção A: Hostinger Python Hosting**
1. **Upgrade para Python Hosting**
   - Hostinger → Painel → Upgrade Plan
   - Escolher "Python Hosting" ou "VPS"
   - Custo: ~R$ 15-30/mês

2. **Configuração automática**
   - Python 3.x pré-instalado
   - pip disponível
   - Deploy direto via SSH

### **Opção B: Aplicação PHP (Conversão)**
Converter Flask para PHP simples:

**Arquivo index.php:**
```php
<?php
session_start();

// WitePay Configuration
$WITEPAY_API_KEY = 'wtp_7819b0bb469f4b52a96feca4ddc46ba4';
$GOOGLE_PIXEL_ID = '6859ccee5af20eab22a408ef';

// Página inicial ENCCEJA
if (!isset($_GET['page'])) {
    include 'templates/index.html';
    exit;
}

// Processar pagamento PIX
if ($_GET['page'] == 'pagamento' && $_POST) {
    $nome = $_POST['nome'];
    $cpf = $_POST['cpf'];
    
    // Chamar API WitePay
    $curl = curl_init();
    curl_setopt_array($curl, [
        CURLOPT_URL => 'https://api.witepay.com.br/v1/order/create',
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'x-api-key: ' . $WITEPAY_API_KEY,
            'Content-Type: application/json'
        ],
        CURLOPT_POSTFIELDS => json_encode([
            'productData' => [[
                'name' => 'Receita do Amor',
                'value' => 9340
            ]],
            'clientData' => [
                'clientName' => $nome,
                'clientDocument' => preg_replace('/\D/', '', $cpf),
                'clientEmail' => 'gerarpagamentos@gmail.com',
                'clientPhone' => '11987790088'
            ]
        ])
    ]);
    
    $response = curl_exec($curl);
    $orderData = json_decode($response, true);
    
    if ($orderData && isset($orderData['orderId'])) {
        // Criar cobrança PIX
        curl_setopt($curl, CURLOPT_URL, 'https://api.witepay.com.br/v1/charge/create');
        curl_setopt($curl, CURLOPT_POSTFIELDS, json_encode([
            'orderId' => $orderData['orderId'],
            'paymentMethod' => 'PIX'
        ]));
        
        $chargeResponse = curl_exec($curl);
        $chargeData = json_decode($chargeResponse, true);
        
        if ($chargeData && isset($chargeData['pixCode'])) {
            $_SESSION['pix_code'] = $chargeData['pixCode'];
            $_SESSION['charge_id'] = $chargeData['id'];
            header('Location: ?page=pagamento&success=1');
            exit;
        }
    }
    
    curl_close($curl);
}

// Mostrar resultado PIX
if ($_GET['page'] == 'pagamento') {
    $pixCode = $_SESSION['pix_code'] ?? null;
    $chargeId = $_SESSION['charge_id'] ?? null;
    include 'templates/pagamento.html';
    exit;
}
?>
```

### **Opção C: Vercel Deploy (Mais Fácil)**
```bash
# No seu computador local:
npm install -g vercel
vercel login
vercel --prod

# Configurar variáveis:
vercel env add WITEPAY_API_KEY
vercel env add SESSION_SECRET
```

**Resultado:** `https://seu-projeto.vercel.app`

### **Opção D: Railway (Python Gratuito)**
1. **Criar conta:** railway.app
2. **Conectar GitHub:** Upload do projeto
3. **Deploy automático:** Reconhece Flask
4. **Configurar variáveis:**
   - WITEPAY_API_KEY
   - SESSION_SECRET

### **Opção E: PythonAnywhere (Especializado)**
1. **Conta gratuita:** pythonanywhere.com
2. **Upload via dashboard**
3. **Python 3.x incluído**
4. **Flask configurado automaticamente**

## 🚀 Recomendação

**Para usar hoje:** Vercel (5 minutos)
**Para produção:** Railway ou PythonAnywhere
**Se quer ficar na Hostinger:** Upgrade para Python Hosting

## 📱 Opção Vercel - Passo a Passo

1. **Criar vercel.json:**
```json
{
  "version": 2,
  "builds": [{"src": "main.py", "use": "@vercel/python"}],
  "routes": [{"src": "/(.*)", "dest": "main.py"}]
}
```

2. **Deploy:**
```bash
vercel --prod
```

3. **Configurar secrets:**
```bash
vercel env add WITEPAY_API_KEY
# Valor: wtp_7819b0bb469f4b52a96feca4ddc46ba4

vercel env add SESSION_SECRET  
# Valor: 8f2e7c4a9b1d6e3f0c5a8b2e9f7c4d1a6b3e0c9f7d4a1b8e5c2f9d6a3b0e7c4f1
```

**Pronto! Site no ar em 5 minutos.**

Qual opção prefere usar?