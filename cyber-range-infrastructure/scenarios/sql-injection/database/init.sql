-- Initialize database for SQL injection challenge
CREATE DATABASE IF NOT EXISTS challenge_db;
USE challenge_db;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL,
    role VARCHAR(20) NOT NULL,
    email VARCHAR(100)
);

-- Flags table
CREATE TABLE IF NOT EXISTS flags (
    flag_id INT PRIMARY KEY,
    flag_value VARCHAR(100) NOT NULL,
    description TEXT
);

-- Insert sample users
INSERT INTO users (username, password, role, email) VALUES
('john', 'john123', 'user', 'john@example.com'),
('alice', 'alice456', 'user', 'alice@example.com'),
('admin', 'impossible_password_12345', 'admin', 'admin@example.com');

-- Insert flag (will be replaced with unique flag per student)
INSERT INTO flags (flag_id, flag_value, description) VALUES
(1, 'FLAG{default_flag_replace_me}', 'Main challenge flag');

-- Show tables for debugging
SHOW TABLES;
SELECT * FROM users;


