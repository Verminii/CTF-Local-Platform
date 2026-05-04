<?php
header('Content-Type: application/json');
header('Cache-Control: no-store');

session_start();
if (!isset($_SESSION['user'])) {
    http_response_code(403);
    echo json_encode(['error' => 'Unauthorized']);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// dopuszczamy localhost i 127.0.0.1 w dowolnym porcie
$origin = $_SERVER['HTTP_ORIGIN'] ?? $_SERVER['HTTP_REFERER'] ?? '';

if ($origin && !(
    strpos($origin, 'http://localhost') === 0 ||
    strpos($origin, 'http://127.0.0.1') === 0
)) {
    http_response_code(403);
    echo json_encode(['error' => 'Forbidden origin']);
    exit;
}

try {
    // === nowa baza flags.db, nie users.db ===
    $pdo = new PDO('sqlite:flags.db');
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

    $stmt = $pdo->query("SELECT flag FROM REDflags WHERE id = 1");
    $row  = $stmt->fetch();
    if (!$row) {
        echo json_encode(['error' => 'No flag found']);
        exit;
    }

    echo json_encode(['flag' => $row['flag']]);
} catch (Exception $e) {
    error_log('DB error (flags.db): ' . $e->getMessage());
    echo json_encode(['error' => 'DB error']);
}
?>
