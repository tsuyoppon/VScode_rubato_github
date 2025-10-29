#!/bin/bash
# EC2 Deployment Script for Rubato Streamlit App
# Optimized for t3.medium instances (4GB RAM, 2 vCPU)

set -e  # Exit on any error

echo "🚀 Starting EC2 deployment for Rubato Streamlit App (t3.medium optimized)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_URL="https://github.com/tsuyoppon/VScode_rubato_github.git"
BRANCH="feature/ec2-minimal-deployment"
APP_NAME="rubato-streamlit"
CONTAINER_NAME="rubato-app"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please do not run this script as root"
    exit 1
fi

# Update system packages
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    print_status "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
    print_status "Docker installed. Please logout and login again to use Docker without sudo."
else
    print_status "Docker is already installed"
fi

# Install Git LFS if not present
if ! command -v git-lfs &> /dev/null; then
    print_status "Installing Git LFS..."
    sudo apt install -y git-lfs
    git lfs install
else
    print_status "Git LFS is already installed"
fi

# Clone or update repository
if [ -d "VScode_rubato_github" ]; then
    print_status "Updating existing repository..."
    cd VScode_rubato_github
    git stash
    git pull origin $BRANCH
    git lfs pull
    cd ..
else
    print_status "Cloning repository..."
    git clone -b $BRANCH $REPO_URL VScode_rubato_github
    cd VScode_rubato_github
    git lfs pull
    cd ..
fi

# Stop and remove existing container
if docker ps -a --format 'table {{.Names}}' | grep -q $CONTAINER_NAME; then
    print_status "Stopping existing container..."
    docker stop $CONTAINER_NAME || true
    docker rm $CONTAINER_NAME || true
fi

# Remove old image
if docker images --format 'table {{.Repository}}:{{.Tag}}' | grep -q $APP_NAME; then
    print_status "Removing old image..."
    docker rmi $APP_NAME:latest || true
fi

# Build Docker image
print_status "Building Docker image..."
cd VScode_rubato_github
docker build -t $APP_NAME:latest .

# Run container
print_status "Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    --restart unless-stopped \
    -p 8501:8501 \
    $APP_NAME:latest

# Wait for container to start
print_status "Waiting for container to start..."
sleep 10

# Check container status
if docker ps --format 'table {{.Names}}\t{{.Status}}' | grep -q $CONTAINER_NAME; then
    print_status "✅ Container is running successfully!"
    print_status "🌐 Application is available at: http://$(curl -s http://checkip.amazonaws.com/):8501"
    
    # Show container logs
    print_status "Recent logs:"
    docker logs --tail 20 $CONTAINER_NAME
else
    print_error "❌ Container failed to start"
    print_error "Container logs:"
    docker logs $CONTAINER_NAME
    exit 1
fi

print_status "🎉 Deployment completed successfully!"
print_status "To view live logs: docker logs -f $CONTAINER_NAME"
print_status "To stop the app: docker stop $CONTAINER_NAME"
