<?php
// login.php
error_reporting(E_ALL);
ini_set('display_errors', 1);

session_start();

// jeśli zalogowany → zniszcz sesję
if (isset($_SESSION['user'])) {
    session_destroy();
    session_start();
}

$msg = '';

$pdo = new PDO('sqlite:users.db');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim($_POST['username'] ?? '');
    $password = trim($_POST['password'] ?? '');

    // zabezpieczenie przeciwko 1=1
    if (stripos($password, '1=1') !== false) {
        $msg = 'This site is secured from 1=1 attack!';
    } else {
        $sql = "SELECT 1 AS success FROM users WHERE username = '$username' AND password = '$password'";
        $stmt = $pdo->query($sql);
        $row = $stmt->fetch();

        if ($row && $row['success'] == 1) {
            $_SESSION['user'] = [
                'id'       => 1,
                'username' => $username
            ];
            header('Location: index.php');
            exit;
        } else {
            $msg = 'Invalid username or password.';
        }
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Login - RE Forum</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body class="re-theme">
  <div class="login-box re-wesker">
    <h1>Enter System</h1>
    <?php if ($msg): ?>
      <p style="color: #f00;"><?= htmlspecialchars($msg) ?></p>
    <?php endif; ?>
    <form method="POST">
      <label>Username</label>
      <input type="text" name="username" required />

      <label>Password</label>
      <input type="password" name="password" required />

      <button type="submit">Login</button>
    </form>
  </div>
</body>
</html>
