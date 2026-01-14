#!/bin/bash
# TERA Deployment Script
# Deploys entire system to OpenStack server

set -e

SERVER="ubuntu@141.100.238.104"
KEY="../terraform/keys/geospatial-key.pem"
REMOTE_DIR="/data/tera"

echo "🚀 TERA Deployment Starting..."
echo "================================"

# 1. Create remote directory structure
echo "📁 Creating directory structure..."
ssh -i $KEY $SERVER "mkdir -p $REMOTE_DIR/{backend,frontend,docker,data,logs}"

# 2. Copy all files
echo "📦 Copying files to server..."
scp -i $KEY -r ./docker-compose.yml $SERVER:$REMOTE_DIR/
scp -i $KEY -r ./docker/ $SERVER:$REMOTE_DIR/
scp -i $KEY -r ./backend/ $SERVER:$REMOTE_DIR/

# 3. Install system dependencies
echo "🔧 Installing system dependencies..."
ssh -i $KEY $SERVER << 'ENDSSH'
cd /data/tera

# Update system
sudo apt-get update -qq

# Install Docker Compose V2 if not present
if ! docker compose version &> /dev/null; then
    sudo apt-get install -y docker-compose-plugin
fi

# Make scripts executable
chmod +x backend/*.sh 2>/dev/null || true

echo "✓ System dependencies installed"
ENDSSH

# 4. Start services
echo "🐳 Starting Docker services..."
ssh -i $KEY $SERVER << 'ENDSSH'
cd /data/tera

# Start infrastructure first
docker compose up -d postgres redis chromadb

echo "⏳ Waiting for databases to be ready..."
sleep 15

# Pull Ollama model (this takes time!)
echo "🤖 Pulling LLM model (this may take a while)..."
docker compose up -d ollama
sleep 5
docker exec tera-ollama ollama pull llama3.1:8b || echo "Model pull will continue in background"

# Start backend
docker compose up -d backend celery-worker

echo ""
echo "✓ Services started"
docker compose ps
ENDSSH

echo ""
echo "================================"
echo "✅ TERA Deployment Complete!"
echo ""
echo "📊 Access Points:"
echo "   API:      http://141.100.238.104:8080"
echo "   API Docs: http://141.100.238.104:8080/docs"
echo "   Health:   http://141.100.238.104:8080/health"
echo ""
echo "🔧 Management Commands:"
echo "   ssh -i $KEY $SERVER 'cd /data/tera && docker compose logs -f'"
echo "   ssh -i $KEY $SERVER 'cd /data/tera && docker compose restart backend'"
echo ""

