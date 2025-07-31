#!/bin/bash
set -e

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
DOCKER_CONFIG="$PROJECT_ROOT/config/docker"

echo "🚀 Starting blockchain news platform deployment..."
echo "📁 Project root: $PROJECT_ROOT"
echo "🐳 Docker config: $DOCKER_CONFIG"

# Change to docker config directory
cd "$DOCKER_CONFIG"

# Create external networks and volumes if they don't exist
echo "📡 Creating external networks and volumes..."
docker network create web 2>/dev/null || echo "Web network already exists"
docker volume create traefik_data 2>/dev/null || echo "Traefik data volume already exists"
docker volume create n8n_data 2>/dev/null || echo "N8N data volume already exists"

# Stop existing services
echo "🛑 Stopping existing services..."
docker compose down --remove-orphans 2>/dev/null || echo "No existing services to stop"

# Build and start services
echo "🔨 Building and starting services..."
docker build -t blockchain-news-platform .
docker compose up -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🔍 Checking service status..."
docker compose ps

echo "🌐 Testing domain access..."
curl -I https://blockchainlatestnews.com/ 2>/dev/null || echo "Domain not ready yet"

echo "✅ Deployment complete!"
echo "📋 Access your services:"
echo "  🌍 Website: https://blockchainlatestnews.com/"
echo "  ⚙️ N8N Dashboard: https://n8n.srv922004.hstgr.cloud/"
echo "  📊 Admin Panel: https://blockchainlatestnews.com/admin/"
echo "  🔧 Traefik Dashboard: http://localhost:8080/"
