#!/bin/bash
# Deploy script for Newave Land Design on EC2
set -e

APP_DIR="/opt/newave-land-design"
REPO_URL="https://github.com/boazeng/newave-land-design.git"

echo "=== Newave Land Design - Deploy Script ==="

# 1. Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx certbot python3-certbot-nginx git

# 2. Clone or update repo
if [ -d "$APP_DIR" ]; then
    echo "Updating existing installation..."
    cd "$APP_DIR"
    git pull origin main
else
    echo "Cloning repo..."
    sudo mkdir -p "$APP_DIR"
    sudo chown $USER:$USER "$APP_DIR"
    git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"

# 3. Set up Python virtual environment
echo "Setting up Python environment..."
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt

# 4. Build frontend (if Node.js available)
if command -v node &> /dev/null; then
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
else
    echo "Node.js not found. Install it or copy pre-built dist/ folder."
    echo "To install: curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash - && sudo apt-get install -y nodejs"
fi

# 5. Set up env file
if [ ! -f "$APP_DIR/env/.env" ]; then
    echo "WARNING: No .env file found at $APP_DIR/env/.env"
    echo "Create it with Priority, SharePoint, and API credentials."
    mkdir -p "$APP_DIR/env"
fi

# 6. Configure Nginx
echo "Configuring Nginx..."
sudo cp deploy/nginx.conf /etc/nginx/sites-available/newave
sudo ln -sf /etc/nginx/sites-available/newave /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl reload nginx

# 7. Set up systemd service
echo "Setting up systemd service..."
sudo cp deploy/newave.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable newave
sudo systemctl restart newave

echo ""
echo "=== Deployment complete ==="
echo "Backend: http://localhost:8001/api/health"
echo "Frontend: http://$(curl -s ifconfig.me)"
echo ""
echo "Next steps:"
echo "1. Point DNS for newave.co.il to this server's IP"
echo "2. Run: sudo certbot --nginx -d newave.co.il -d www.newave.co.il"
echo "3. Uncomment HTTPS section in /etc/nginx/sites-available/newave"
