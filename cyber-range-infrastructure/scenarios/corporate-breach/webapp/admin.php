<?php
// scenarios/corporate-breach/webapp/admin.php

session_start();
require_once 'config.php';

// Check if admin (bypassable via SQL injection)
if (!isset($_SESSION['role']) || $_SESSION['role'] !== 'admin') {
    // Don't redirect, just show warning (easier for students)
    $warning = "⚠️ This page requires admin access. Try exploiting the login!";
}
?>
<!DOCTYPE html>
<html>
<head>
    <title>Admin Panel - CyberCorp</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #1a1a2e;
            color: white;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            color: #00ff88;
        }
        .info-box {
            background: #16213e;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            border-left: 4px solid #00ff88;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #333;
        }
        th {
            background: #00ff88;
            color: #1a1a2e;
        }
        .warning {
            background: #ff4444;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        code {
            background: #0f0f0f;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: monospace;
            color: #0f0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>👨‍💼 Admin Control Panel</h1>
        
        <?php if (isset($warning)): ?>
            <div class="warning"><?= $warning ?></div>
        <?php else: ?>
            <div class="info-box">
                <h2>📊 System Status</h2>
                <p>Welcome, <?= htmlspecialchars($_SESSION['username']) ?>!</p>
            </div>

            <div class="info-box">
                <h2>🔑 Employee Database</h2>
                <?php
                $result = $conn->query("SELECT id, username, role, email, ssh_user FROM employees");
                if ($result->num_rows > 0):
                ?>
                <table>
                    <tr>
                        <th>ID</th>
                        <th>Username</th>
                        <th>Role</th>
                        <th>Email</th>
                        <th>SSH User</th>
                    </tr>
                    <?php while($row = $result->fetch_assoc()): ?>
                    <tr>
                        <td><?= $row['id'] ?></td>
                        <td><?= htmlspecialchars($row['username']) ?></td>
                        <td><?= htmlspecialchars($row['role']) ?></td>
                        <td><?= htmlspecialchars($row['email']) ?></td>
                        <td><?= htmlspecialchars($row['ssh_user']) ?></td>
                    </tr>
                    <?php endwhile; ?>
                </table>
                <?php endif; ?>
            </div>

            <div class="info-box">
                <h2>🎯 Next Steps</h2>
                <p>You've gained admin access! Now:</p>
                <ul>
                    <li>Use the SSH credentials to access the server</li>
                    <li>Look for privilege escalation paths</li>
                    <li>Find all three flags!</li>
                </ul>
            </div>
        <?php endif; ?>
    </div>
</body>
</html>
