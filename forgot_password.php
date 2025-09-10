<?php
session_start();
require_once 'config/database.php';

$message = '';
$error = '';

if ($_POST) {
    $email = trim($_POST['email'] ?? '');
    
    if ($email && filter_var($email, FILTER_VALIDATE_EMAIL)) {
        $db = getDB();
        if ($db) {
            // Find user by email
            $user_doc = $db->users->findOne(['email' => $email]);
            
            if ($user_doc) {
                $user = mongoToArray($user_doc);
                
                // Generate secure reset token
                $reset_token = bin2hex(random_bytes(32));
                $reset_expires = new MongoDB\BSON\UTCDateTime((time() + 3600) * 1000); // 1 hour from now
                
                // Store reset token in database
                $db->users->updateOne(
                    ['id' => $user['id']],
                    ['$set' => [
                        'reset_token' => $reset_token,
                        'reset_expires' => $reset_expires,
                        'reset_requested_at' => new MongoDB\BSON\UTCDateTime()
                    ]]
                );
                
                // In a real application, you would send an email here
                // For now, we'll show the reset link (in production, only send via email)
                $reset_url = "https://" . $_SERVER['HTTP_HOST'] . "/reset_password.php?token=" . $reset_token;
                
                $message = "Password reset instructions have been sent to your email address. " .
                          "<br><br><strong>Development Mode:</strong> Use this link to reset your password:<br>" .
                          "<a href='" . $reset_url . "' class='btn btn-primary btn-sm mt-2'>Reset Password</a>";
            } else {
                // Don't reveal whether email exists or not for security
                $message = "If an account with this email exists, password reset instructions have been sent.";
            }
        } else {
            $error = 'Database connection failed';
        }
    } else {
        $error = 'Please enter a valid email address';
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Forgot Password - Tax Sale Compass</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
        }
        .reset-card {
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
    </style>
</head>
<body>
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-6 col-lg-4">
                <div class="reset-card p-4">
                    <div class="text-center mb-4">
                        <h2 class="fw-bold text-primary">Reset Password</h2>
                        <p class="text-muted">Enter your email to receive reset instructions</p>
                    </div>

                    <?php if ($error): ?>
                        <div class="alert alert-danger" role="alert">
                            <?php echo htmlspecialchars($error); ?>
                        </div>
                    <?php endif; ?>

                    <?php if ($message): ?>
                        <div class="alert alert-success" role="alert">
                            <?php echo $message; ?>
                        </div>
                    <?php else: ?>
                        <form method="POST">
                            <div class="mb-3">
                                <label for="email" class="form-label">Email Address</label>
                                <input type="email" class="form-control" id="email" name="email" 
                                       value="<?php echo htmlspecialchars($_POST['email'] ?? ''); ?>" 
                                       placeholder="Enter your email address" required>
                            </div>
                            
                            <button type="submit" class="btn btn-primary w-100">Send Reset Instructions</button>
                        </form>
                    <?php endif; ?>
                    
                    <div class="text-center mt-3">
                        <a href="login.php" class="btn btn-link">← Back to Login</a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>