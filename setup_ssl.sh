#!/bin/bash

# SSL Setup Script for ELO Rating System
echo "🔐 Setting up SSL certificate..."

# Check if we have a domain name
if [ -z "$1" ]; then
    echo "Usage: $0 <domain-name>"
    echo "Example: $0 elo.yourdomain.com"
    echo ""
    echo "If you don't have a domain, you can:"
    echo "1. Use a free service like DuckDNS"
    echo "2. Set up a subdomain in your DNS"
    echo "3. Use the EC2 hostname (less secure)"
    exit 1
fi

DOMAIN=$1

# Install certbot if not installed
if ! command -v certbot &> /dev/null; then
    echo "Installing certbot..."
    sudo yum update -y
    sudo yum install -y certbot
fi

# Stop any running server
echo "Stopping existing server..."
pkill -f "python.*server.py" || true

# Get SSL certificate using standalone mode
echo "Getting SSL certificate for $DOMAIN..."
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --http-01-port 80 \
    -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    --email your-email@example.com

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully!"
    echo "Certificate files are in /etc/letsencrypt/live/$DOMAIN/"
    
    # Set up certificate renewal
    echo "Setting up automatic renewal..."
    (sudo crontab -l 2>/dev/null; echo "0 12 * * * /usr/bin/certbot renew --quiet") | sudo crontab -
    
    echo "🎉 SSL setup complete!"
    echo "Update your server.py to use:"
    echo "ssl_context=('/etc/letsencrypt/live/$DOMAIN/fullchain.pem', '/etc/letsencrypt/live/$DOMAIN/privkey.pem')"
else
    echo "❌ Failed to get SSL certificate"
    echo "Make sure:"
    echo "1. Port 80 is open in your security group"
    echo "2. Domain $DOMAIN points to this server"
    echo "3. No other service is using port 80"
fi