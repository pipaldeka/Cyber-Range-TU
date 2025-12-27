<?php
// scenarios/corporate-breach/webapp/config.php

$host = getenv('DB_HOST') ?: 'localhost';
$user = getenv('DB_USER') ?: 'webapp_user';
$pass = getenv('DB_PASS') ?: 'webapp_password_123';
$db   = getenv('DB_NAME') ?: 'corporate_db';

// Create connection
$conn = new mysqli($host, $user, $pass, $db);

// Check connection
if ($conn->connect_error) {
    die("Database connection failed: " . $conn->connect_error);
}
?>
