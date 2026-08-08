#!/bin/bash
set -e

# Update and install Docker & Docker Compose
apt-get update -y
apt-get install -y ca-certificates curl gnupg lsb-release git

mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null

apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Clone FinOps Project and start Docker Compose
mkdir -p /opt/finops
cd /opt/finops

# Generate Production .env file
cat <<EOF > .env
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0
DATABASE_URL=sqlite+aiosqlite:///./data/finops.db
GEMINI_API_KEY=${GEMINI_API_KEY}
GEMINI_MODEL=gemini-2.0-flash
TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
TELEGRAM_MODE=polling
ERPNEXT_MODE=mock
MAX_AUTO_REFUND_LIMIT=200.00
MAX_FRAUD_RISK_THRESHOLD=0.30
EOF

# Ensure data directory exists for database persistence
mkdir -p /opt/finops/data

# Pull pre-built containers from Docker Hub (suryadocker0) and run
cat <<EOF > docker-compose.yml
version: '3.8'

services:
  backend:
    image: suryadocker0/finops-backend:latest
    container_name: finops-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    image: suryadocker0/finops-frontend:latest
    container_name: finops-frontend
    ports:
      - "80:80"
      - "3000:80"
    depends_on:
      - backend
    restart: unless-stopped

networks:
  default:
    name: finops-net
EOF

docker compose up -d

