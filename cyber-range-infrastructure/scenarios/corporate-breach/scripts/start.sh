#!/bin/bash
# scenarios/corporate-breach/scripts/start.sh

# Initialize MySQL
service mysql start

# Wait for MySQL to be ready
sleep 5

# Initialize database
mysql < /docker-entrypoint-initdb.d/init.sql

# Create MySQL user for web app
mysql -e "CREATE USER IF NOT EXISTS 'webapp_user'@'localhost' IDENTIFIED BY 'webapp_password_123';"
mysql -e "GRANT ALL PRIVILEGES ON corporate_db.* TO 'webapp_user'@'localhost';"
mysql -e "FLUSH PRIVILEGES;"

# Start SSH
service ssh start

# Start Apache in foreground
apache2ctl -D FOREGROUND
