#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update -y
sudo apt-get install -y git docker.io curl
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker "$USER"

echo "Docker installed. Log out and SSH back in, or run: newgrp docker"
docker --version || true
