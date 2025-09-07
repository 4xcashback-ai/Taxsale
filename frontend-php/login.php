<?php
session_start();
require_once 'config/database.php';

$error = '';

if ($_POST) {
    $email = $_POST['email'] ?? '';
    $password = $_POST['password'] ?? '';
    
    if ($email && $password) {
        // Call backend API for authentication
        $api_url = API_BASE_URL . '/auth/login';
        
        $data = json_encode([
            'email' => $email,
            'password' => $password
        ]);
        
        $context = stream_context_create([
            'http' => [
                'method' => 'POST',
                'header' => 'Content-Type: application/json',
                'content' => $data
            ]
        ]);
        
        $response = file_get_contents($api_url, false, $context);
        
        if ($response) {
            $result = json_decode($response, true);
            
            if (isset($result['access_token'])) {
                // Store user data in session
                $_SESSION['user_id'] = $result['user']['email'];
                $_SESSION['access_token'] = $result['access_token'];
                $_SESSION['subscription_tier'] = $result['user']['subscription_tier'];
                $_SESSION['is_admin'] = $result['user']['is_admin'];
                
                // Redirect to intended page or search page
                $redirect = $_GET['redirect'] ?? 'search.php';
                header('Location: ' . $redirect);
                exit;
            } else {
                $error = 'Invalid credentials';
            }
        } else {
            $error = 'Login service unavailable';
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