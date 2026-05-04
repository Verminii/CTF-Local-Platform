<?php
session_start();

if (!isset($_SESSION['user'])) {
    header('Location: login.php');
    exit;
}

$msg = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $content = trim($_POST['content'] ?? '');

    if (empty($content)) {
        $msg = 'Post content cannot be empty.';
    } else {
        $content = preg_replace_callback(
            '/<script\b[^>]*>([\s\S]*?)<\/script>/is',
            function ($matches) {
                $inner = $matches[1];
                $sanitized = preg_replace('/[a-zA-Z]/', 'A', $inner);
                $tag = $matches[0];
                $pos = strpos($tag, '>');
                $prefix = substr($tag, 0, $pos + 1);
                $suffix = substr($tag, $pos + 1);
                $posClose = strpos($suffix, '</script>');
                $suffix = substr($suffix, $posClose);
                return $prefix . $sanitized . $suffix;
            },
            $content
        );

        $postsFile = 'posts.json';
        $posts = json_decode(file_get_contents($postsFile), true) ?: [];

        if (!is_array($posts)) {
            $posts = [];
        }

        $id = 1;
        if (!empty($posts)) {
            $ids = array_column($posts, 'id');
            $id = max($ids) + 1;
        }

        $new_post = [
            'id'        => $id,
            'author'    => $_SESSION['user']['username'],
            'content'   => $content,
            'timestamp' => date('Y-m-d H:i:s')
        ];

        $posts[] = $new_post;

        if (file_put_contents($postsFile, json_encode($posts, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE))) {
            header('Location: index.php');
            exit;
        } else {
            $msg = 'Failed to save post.';
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Create Post</title>
  <link rel="stylesheet" href="style.css" />
</head>
<body class="re-theme">
  <div class="top-bar">
    <h1>Create New Post</h1>
    <div class="nav-links">
      <span>Logged in as: <?= htmlspecialchars($_SESSION['user']['username']) ?></span>
      <a href="index.php" class="nav-btn">← Back to forum</a>
    </div>
  </div>

  <?php if (isset($msg)): ?>
    <p style="color: #f00;"><?= htmlspecialchars($msg) ?></p>
  <?php endif; ?>

  <form method="POST" class="create-post-form">
    <textarea
      name="content"
      placeholder="Write your post (HTML decorators like <a>, <h1> allowed, but don't minnd about using &lt;script&gt;! It is sanitized anyway"
      required
    ></textarea>
    <div>
      <button type="submit">Publish</button>
    </div>
  </form>
</body>
</html>
