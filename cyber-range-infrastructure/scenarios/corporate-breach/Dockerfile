# scenarios/corporate-breach/Dockerfile

FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install all required packages
RUN apt-get update && apt-get install -y \
    apache2 \
    php \
    libapache2-mod-php \
    php-mysql \
    mysql-server \
    openssh-server \
    sudo \
    vim \
    nano \
    curl \
    wget \
    net-tools \
    python3 \
    python3-pip \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Configure SSH
RUN mkdir /var/run/sshd
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config

# Create users with different privilege levels
RUN useradd -m -s /bin/bash webadmin && echo 'webadmin:WebAdmin2024!' | chpasswd
RUN useradd -m -s /bin/bash developer && echo 'developer:DevSecure99' | chpasswd
RUN useradd -m -s /bin/bash dbuser && echo 'dbuser:DatabaseUser123' | chpasswd

# Configure sudo (VULNERABILITY: misconfigured sudo)
RUN echo 'developer ALL=(ALL) NOPASSWD: /usr/bin/vim' >> /etc/sudoers
RUN echo 'webadmin ALL=(dbuser) NOPASSWD: /usr/bin/mysql' >> /etc/sudoers

# Copy web application
COPY webapp/ /var/www/html/
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html
RUN mkdir -p /var/www/html/uploads
RUN chmod 777 /var/www/html/uploads

# Copy database initialization
COPY database/init.sql /docker-entrypoint-initdb.d/

# Copy scripts
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# VULNERABILITY 1: SUID binary (backup script)
RUN cp /bin/bash /usr/local/bin/backup_util
RUN chmod 4755 /usr/local/bin/backup_util
RUN chown root:root /usr/local/bin/backup_util

# VULNERABILITY 2: World-writable script called by root cron
RUN echo '#!/bin/bash\necho "Backup running..." >> /var/log/backup.log' > /usr/local/bin/cleanup.sh
RUN chmod 777 /usr/local/bin/cleanup.sh
RUN chown root:root /usr/local/bin/cleanup.sh

# VULNERABILITY 3: Sensitive file with weak permissions
RUN echo 'DATABASE_PASSWORD=SuperSecret2024!' > /opt/db_backup_config.txt
RUN chmod 644 /opt/db_backup_config.txt

# Create flags at different privilege levels
RUN mkdir -p /flags
RUN echo 'FLAG{user_level_access_achieved}' > /flags/flag1.txt
RUN chown webadmin:webadmin /flags/flag1.txt
RUN chmod 600 /flags/flag1.txt

RUN echo 'FLAG{database_credentials_compromised}' > /flags/flag2.txt
RUN chown developer:developer /flags/flag2.txt
RUN chmod 600 /flags/flag2.txt

RUN echo 'FLAG{root_access_game_over}' > /root/flag3.txt
RUN chmod 600 /root/flag3.txt

# Apache configuration
RUN a2enmod rewrite
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Expose ports
EXPOSE 80 22

# Start script
CMD ["/usr/local/bin/start.sh"]
