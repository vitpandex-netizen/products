#!/bin/bash
# Deploy script for Oracle VPS
# Использование: ./deploy.sh <domain>

set -e

DOMAIN=${1:-chat.yourdomain.com}
APP_DIR=/opt/multi-agent-chat

echo "🚀 Deploying Multi-Agent Chat to $DOMAIN"

# 1. Install Docker if not present
if ! command -v docker &>/dev/null; then
    echo "📦 Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker $USER
fi

# 2. Clone/copy application
echo "📁 Setting up $APP_DIR..."
sudo mkdir -p $APP_DIR
sudo rsync -av --exclude='node_modules' --exclude='data' --exclude='.env' \
    ./ $APP_DIR/

# 3. Set up .env
if [ ! -f "$APP_DIR/.env" ]; then
    echo "📝 Creating .env..."
    JWT_SECRET=$(openssl rand -hex 64)
    sudo tee $APP_DIR/.env > /dev/null << EOF
PORT=5555
JWT_SECRET=${JWT_SECRET}
OPENROUTER_API_KEY=${OPENROUTER_API_KEY:-}
EOF
fi

# 4. Start with Docker Compose
echo "🐳 Starting Docker container..."
cd $APP_DIR && sudo docker-compose up -d --build

# 5. Install Nginx
echo "🌐 Setting up Nginx..."
sudo apt-get update -qq
sudo apt-get install -y -qq nginx certbot python3-certbot-nginx

# 6. Configure Nginx
sudo sed -i "s/chat.yourdomain.com/$DOMAIN/g" $APP_DIR/deploy/nginx.conf
sudo ln -sf $APP_DIR/deploy/nginx.conf /etc/nginx/sites-available/multi-agent-chat
sudo ln -sf /etc/nginx/sites-available/multi-agent-chat /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 7. Let's Encrypt
echo "🔒 Obtaining SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos --email admin@$DOMAIN || true

# 8. Set up auto-renewal
echo "🔄 Setting up certbot auto-renewal..."
sudo systemctl enable certbot.timer || true

echo ""
echo "✅ Deployment complete!"
echo "🌐 Open https://$DOMAIN"
echo "📋 Login: admin / admin123"
echo "⚠️  CHANGE THE ADMIN PASSWORD IMMEDIATELY!"
