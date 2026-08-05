#!/usr/bin/env bash
# scripts/redeploy_docker_compose.sh
# Usage: run from repository root on the host where docker-compose.yml is located

set -euo pipefail

echo "Pulling latest from git..."
if [ -d .git ]; then
  git pull origin main || true
fi

echo "Building and restarting docker-compose service..."
if command -v docker-compose >/dev/null 2>&1; then
  docker-compose build --no-cache web || true
  docker-compose up -d --force-recreate --remove-orphans
  docker-compose logs -f --tail=200 web
else
  echo "docker-compose not found. If you use docker, run: docker restart <container>"
fi
