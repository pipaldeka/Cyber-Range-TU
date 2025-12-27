<!DOCTYPE html>
<html>
<head>
    <title>Vulnerable Login - SQL Injection Challenge</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
            width: 400px;
        }
        h1 {
            color: #333;
            text-align: center;
            margin-bottom: 30px;
        }
        input[type="text"], input[type="password"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 5px;
            box-sizing: border-box;
        }
        button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin-top: 10px;
        }
        button:hover {
            background: #5568d3;
        }
        .error {
            color: red;
            text-align: center;
            margin-top: 10px;
        }
        .success {
            color: green;
            text-align: center;
            margin-top: 10px;
        }
        .hint {
            background: #f0f0f0;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔐 Login Portal</h1>
        
        <?php
        // Database connection
        $host = getenv('DB_HOST') ?: 'database';
        $user = getenv('DB_USER') ?: 'webapp_user';
        $pass = getenv('DB_PASS') ?: 'webapp_pass';
        $db   = getenv('DB_NAME') ?: 'challenge_db';

        $conn = mysqli_connect($host, $user, $pass, $db);

        if (!$conn) {
            die("<div class='error'>Database connection failed!</div>");
        }

        if ($_SERVER['REQUEST_METHOD'] == 'POST') {
            $username = $_POST['username'];
            $password = $_POST['password'];
            
            // VULNERABILITY: No input sanitization!
            // This is intentionally vulnerable to SQL injection
            $query = "SELECT * FROM users WHERE username='$username' AND password='$password'";
            
            // Show the query for educational purposes
            echo "<div class='hint'><strong>Query executed:</strong><br><code>$query</code></div>";
            
            $result = mysqli_query($conn, $query);
            
            if ($result && mysqli_num_rows($result) > 0) {
                $row = mysqli_fetch_assoc($result);
                
                echo "<div class='success'>✅ Login successful!</div>";
                echo "<div class='success'>Welcome, " . htmlspecialchars($row['username']) . "!</div>";
                
                // Check if user is admin
                if ($row['role'] == 'admin') {
                    // Retrieve the flag from database
                    $flag_query = "SELECT flag_value FROM flags WHERE flag_id=1";
                    $flag_result = mysqli_query($conn, $flag_query);
                    
                    if ($flag_result && mysqli_num_rows($flag_result) > 0) {
                        $flag_row = mysqli_fetch_assoc($flag_result);
                        echo "<div class='success' style='font-size: 20px; margin-top: 20px;'>";
                        echo "🚩 FLAG: <strong>" . htmlspecialchars($flag_row['flag_value']) . "</strong>";
                        echo "</div>";
                    }
                } else {
                    echo "<div class='hint'>You're logged in as a regular user. Try to become admin!</div>";
                }
            } else {
                echo "<div class='error'>❌ Invalid credentials!</div>";
            }
        }
        ?>
        
        <form method="POST">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Login</button>
        </form>
        
        <div class="hint">
            <strong>💡 Hint:</strong> Try some SQL injection techniques. 
            Known users: <code>john</code>, <code>admin</code>
        </div>
    </div>
</body>
</html>


