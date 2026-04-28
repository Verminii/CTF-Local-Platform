<?php
// profile.php
session_start();

// jeśli nie zalogowany → do loginu
if (!isset($_SESSION['user'])) {
    header('Location: login.php');
    exit;
}

// nazwa zalogowanego usera
$username = $_SESSION['user']['username'];

$pdo = new PDO('sqlite:users.db');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

$error = null;
$success = null;

// wczytaj opis zalogowanego usera
$stmt = $pdo->prepare("SELECT description FROM users WHERE username = ?");
$stmt->execute([$username]);
$user = $stmt->fetch();

if (!$user) {
    die('User profile not found.');
}

// jeśli user wysłał formularz
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $new_desc = trim($_POST['description'] ?? '');

    if (empty($new_desc)) {
        $error = 'Notes cannot be empty.';
    } else {
        $update_stmt = $pdo->prepare("UPDATE users SET description = ? WHERE username = ?");
        $update_stmt->execute([$new_desc, $username]);
        $success = 'Notes updated.';
        $user['description'] = $new_desc; // odśwież
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Your Notes - <?= htmlspecialchars($username) ?></title>
  <link rel="stylesheet" href="style.css" />
</head>
<body class="re-theme">
  <div class="top-bar">
    <h1>Your Notes - <?= htmlspecialchars($username) ?></h1>
    <div class="nav-links">
      <span>Logged in as: <?= htmlspecialchars($username) ?></span>
      <a href="index.php" class="nav-btn">← Forum</a>
      <a href="index.php?logout" class="nav-btn nav-logout">Logout</a>
    </div>
  </div>

  <main class="profile-page">
    <?php if ($error): ?>
      <p style="color: #f00; margin: 1rem auto; font-size: 0.9rem;"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>

    <?php if ($success): ?>
      <p style="color: #0f0; margin: 1rem auto; font-size: 0.9rem;"><?= htmlspecialchars($success) ?></p>
    <?php endif; ?>

    <h2>Your Notes</h2>

    <form method="POST" class="edit-desc-form">
      <label>Twoje prywatne notatki.
Nikt nie powinien ich zobaczyć… chyba że sam je ujawnisz.</label>
      <textarea name="description" placeholder="Write your notes here..."><?= htmlspecialchars($user['description'] ?? '') ?></textarea>
      <button type="submit">Save</button>
    </form>
  </main>
</body>
</html>
