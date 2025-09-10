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
                
                // Verify password (check both possible field names)
                $password_hash = $user['password_hash'] ?? $user['password'] ?? '';
                $password_valid = false;
                
                if ($password_hash) {
                    // Try modern bcrypt verification first
                    if (password_verify($password, $password_hash)) {
                        $password_valid = true;
                    }
                    // Try legacy hash methods if bcrypt fails
                    elseif (strlen($password_hash) === 64) {
                        // Likely SHA-256 hash - try common formats
                        $legacy_hashes = [
                            hash('sha256', $password),
                            hash('sha256', $password . 'salt'),
                            hash('sha256', 'salt' . $password),
                            md5($password),
                            hash('sha1', $password),
                        ];
                        
                        if (in_array($password_hash, $legacy_hashes)) {
                            $password_valid = true;
                            
                            // Upgrade to modern hash
                            $new_hash = password_hash($password, PASSWORD_DEFAULT);
                            $db->users->updateOne(
                                ['id' => $user['id']],
                                ['$set' => ['password_hash' => $new_hash]]
                            );
                        }
                    }
                    elseif (strlen($password_hash) === 32) {
                        // Likely MD5 hash
                        if ($password_hash === md5($password)) {
                            $password_valid = true;
                            
                            // Upgrade to modern hash
                            $new_hash = password_hash($password, PASSWORD_DEFAULT);
                            $db->users->updateOne(
                                ['id' => $user['id']],
                                ['$set' => ['password_hash' => $new_hash]]
                            );
                        }
                    }
                }
                
                if ($password_valid) {
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
        $error = 'Please enter both username and password';
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login - Tax Sale Compass</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .login-card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1);
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
        }
        .btn-primary:hover {
            background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        }
        .forgot-password-link {
            color: #667eea;
            text-decoration: none;
            font-size: 0.9rem;
        }
        .forgot-password-link:hover {
            color: #5a6fd8;
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="login-card p-4">
                    <div class="text-center mb-4">
                        <h2 class="fw-bold text-primary">Tax Sale Compass</h2>
                        <p class="text-muted">Sign in to your account</p>
                    </div>

                    <?php if ($error): ?>
                        <div class="alert alert-danger" role="alert">
                            <?php echo htmlspecialchars($error); ?>
                        </div>
                    <?php endif; ?>

                    <form method="POST">
                        <div class="mb-3">
                            <label for="username" class="form-label">Email/Username</label>
                            <input type="text" class="form-control" id="username" name="username" 
                                   value="<?php echo htmlspecialchars($_POST['username'] ?? ''); ?>" required>
                        </div>
                        
                        <div class="mb-3">
                            <label for="password" class="form-label">Password</label>
                            <input type="password" class="form-control" id="password" name="password" required>
                        </div>
                        
                        <div class="text-end mb-3">
                            <a href="forgot_password.php" class="forgot-password-link">Forgot Password?</a>
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100">Sign In</button>
                        <div class="text-center mt-3">
                            <a href="register.php" class="btn btn-link">Don't have an account? Register</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>