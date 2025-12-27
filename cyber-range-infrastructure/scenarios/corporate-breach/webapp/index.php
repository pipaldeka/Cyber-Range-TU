<?php
// scenarios/corporate-breach/webapp/index.php
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CyberCorp Solutions - Internal Portal</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .container {
            background: white;
            padding: 50px;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 600px;
            width: 90%;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }
        .subtitle {
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .info-box {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .info-box h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        .info-box ul {
            margin-left: 20px;
            color: #555;
        }
        .info-box ul li {
            margin: 8px 0;
        }
        .btn {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 15px 40px;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px;
            transition: background 0.3s;
            text-align: center;
        }
        .btn:hover {
            background: #5568d3;
        }
        .btn-container {
            text-align: center;
            margin-top: 30px;
        }
        .warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
            color: #856404;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏢 CyberCorp Solutions</h1>
        <p class="subtitle">Internal Employee Portal v2.1</p>
        
        <div class="info-box">
            <h3>📋 Penetration Test Objectives</h3>
            <ul>
                <li><strong>Flag 1:</strong> Gain initial access as a regular user</li>
                <li><strong>Flag 2:</strong> Escalate to developer/dbuser privileges</li>
                <li><strong>Flag 3:</strong> Achieve root access</li>
            </ul>
        </div>

        <div class="info-box">
            <h3>🎯 Attack Surface</h3>
            <ul>
                <li>Web Application (Port 80)</li>
                <li>SSH Service (Port 22)</li>
                <li>MySQL Database (Internal)</li>
            </ul>
        </div>

        <div class="warning">
            <strong>⚠️ Note:</strong> This is an intentionally vulnerable system for training purposes. 
            Explore, enumerate, and escalate carefully!
        </div>

        <div class="btn-container">
            <a href="login.php" class="btn">🔐 Employee Login</a>
            <a href="admin.php" class="btn">👨‍💼 Admin Panel</a>
        </div>
    </div>
</body>
</html>
