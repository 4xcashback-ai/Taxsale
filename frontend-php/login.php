<?php
session_start();
require_once 'config/database.php';

$error = '';

if ($_POST) {
    $username = $_POST['username'] ?? $_POST['email'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($username && $password) {
        // MongoDB authentication
        $db = getDB();
        if ($db) {
            // Find user by username or email
            $user_doc = $db->users->findOne([
                '$or' => [
                    ['username' => $username],
                    ['email' => $username]
                ]
            ]);
            
            if ($user_doc) {
                $user = mongoToArray($user_doc);
                
                // Verify password
                if (password_verify($password, $user['password_hash'])) {
                    // Store user data in session
                    $_SESSION['user_id'] = $user['id'];
                    $_SESSION['access_token'] = 'mongodb_session_' . uniqid();
                    $_SESSION['subscription_tier'] = $user['subscription_tier'];
                    $_SESSION['is_admin'] = $user['is_admin'];
                    $_SESSION['username'] = $user['username'];
                    $_SESSION['email'] = $user['email'];
                    
                    // Redirect to intended page or search page
                    $redirect = $_GET['redirect'] ?? 'search.php';
                    header('Location: ' . $redirect);
                    exit;
                } else {
                    $error = 'Invalid credentials';
                }
            } else {
                $error = 'User not found';
            }
        } else {
            $error = 'Database connection failed';
        }
    } else {
        $error = 'Please fill in all fields';
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - <?php echo SITE_NAME; ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="index.php"><?php echo SITE_NAME; ?></a>
        </div>
    </nav>

    <div class="container mt-5">
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h3>Login</h3>
                    </div>
                    <div class="card-body">
                        <?php if ($error): ?>
                            <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
                        <?php endif; ?>
                        
                        <form method="POST">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email/Username</label>
                                <input type="text" class="form-control" id="email" name="email" 
                                       value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>" required>
                            </div>
                            
                            <div class="mb-3">
                                <label for="password" class="form-label">Password</label>
                                <input type="password" class="form-control" id="password" name="password" required>
                            </div>
                            
                            <button type="submit" class="btn btn-primary">Sign In</button>
                            <a href="register.php" class="btn btn-link">Don't have an account? Register</a>
                        </form>
                        

                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>