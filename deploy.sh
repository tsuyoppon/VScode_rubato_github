#!/bin/bash

# EC2 deployment script for t3.small optimized Rubato app
set -euo pipefail

echo "=== Rubato EC2 Deployment Script ==="

# Update system
echo "Updating system packages..."
sudo apt-get update

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt-get install -y ca-certificates curl gnupg
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker ubuntu
    echo "Docker installed successfully"
else
    echo "Docker is already installed"
fi

# Install Git LFS if not present
if ! command -v git-lfs &> /dev/null; then
    echo "Installing Git LFS..."
    sudo apt-get install -y git-lfs
    git lfs install
    echo "Git LFS installed successfully"
else
    echo "Git LFS is already installed"
fi

# Clone repository
REPO_DIR="/opt/rubato-app"
if [ ! -d "$REPO_DIR" ]; then
    echo "Cloning repository..."
    sudo mkdir -p /opt
    sudo git clone https://github.com/tsuyoppon/VScode_rubato_github.git $REPO_DIR
    sudo chown -R ubuntu:ubuntu $REPO_DIR
    cd $REPO_DIR
    git checkout feature/ec2-minimal-deployment
    git lfs pull
else
    echo "Repository already exists, updating..."
    cd $REPO_DIR
    sudo chown -R ubuntu:ubuntu $REPO_DIR
    git fetch --all
    git checkout feature/ec2-minimal-deployment
    git pull origin feature/ec2-minimal-deployment
    git lfs pull
fi

cd $REPO_DIR

# Stop and remove existing container if exists
echo "Stopping existing container..."
sudo docker stop rubato-app 2>/dev/null || true
sudo docker rm rubato-app 2>/dev/null || true

# Build Docker image
echo "Building Docker image..."
sudo docker build -t rubato-streamlit:latest .

# Run container
echo "Starting container..."
sudo docker run -d \
    --name rubato-app \
    --restart unless-stopped \
    -p 8501:8501 \
    rubato-streamlit:latest

# Wait for container to start
echo "Waiting for container to start..."
sleep 10

# Check container status
if sudo docker ps | grep -q rubato-app; then
    echo "✅ Container started successfully!"
    echo "🌐 Access your app at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8501"
else
    echo "❌ Container failed to start. Checking logs..."
    sudo docker logs rubato-app
    exit 1
fi

echo "=== Deployment Complete ==="
