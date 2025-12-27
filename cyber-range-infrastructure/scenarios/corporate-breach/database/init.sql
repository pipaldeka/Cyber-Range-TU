-- scenarios/corporate-breach/database/init.sql

CREATE DATABASE IF NOT EXISTS corporate_db;
USE corporate_db;

CREATE TABLE IF NOT EXISTS employees (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    ssh_user VARCHAR(50),
    ssh_pass VARCHAR(100)
);

-- Insert employees (passwords are MD5 hashed)
-- Note: MD5 is intentionally weak!
INSERT INTO employees (username, password, role, email, ssh_user, ssh_pass) VALUES
('john', MD5('john123'), 'user', 'john@cybercorp.com', NULL, NULL),
('alice', MD5('alice456'), 'user', 'alice@cybercorp.com', NULL, NULL),
('bob', MD5('bob789'), 'developer', 'bob@cybercorp.com', 'developer', 'DevSecure99'),
('admin', MD5('SuperSecureAdmin2024'), 'admin', 'admin@cybercorp.com', 'webadmin', 'WebAdmin2024!');

-- Create audit log table
CREATE TABLE IF NOT EXISTS audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    action VARCHAR(100),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

SHOW TABLES;
SELECT username, role, ssh_user FROM employees;
