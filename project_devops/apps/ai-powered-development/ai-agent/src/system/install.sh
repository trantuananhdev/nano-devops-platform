#!/bin/bash
# AI-Powered Development (The Ghost Engineer) - One-line Installer
# Usage: curl -sL https://ai.nano.platform/install | sh

set -e

echo "👻 Installing The Ghost Engineer (Agent-Node)..."

# 1. Check for Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# 2. Deploy the Sensor (Agent-Node)
# In a real viral MVP, this would be a pre-built image on Docker Hub
docker run -d \
  --name ghost-engineer-sensor \
  --restart unless-stopped \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -e NODE_NAME=$(hostname) \
  -e BRAIN_URL="https://ai.nano.platform/v1/incidents/report" \
  nanodevops/agent-node:latest

echo "✅ Ghost Engineer Sensor is now haunting your node!"
echo "🕵️ Monitoring for crashes and OOM events..."
