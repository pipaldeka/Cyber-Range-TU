# scenarios/sql-injection/Dockerfile
# ===================================
# PURPOSE: Build vulnerable PHP web application
# BUILT BY: Terraform during deployment
# ===================================

FROM php:7.4-apache

# Install MySQL extension
RUN docker-php-ext-install mysqli pdo pdo_mysql

# Copy web application files
COPY webapp/ /var/www/html/

# Set permissions
RUN chown -R www-data:www-data /var/www/html && \
    chmod -R 755 /var/www/html

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

# Apache runs automatically (from base image)

