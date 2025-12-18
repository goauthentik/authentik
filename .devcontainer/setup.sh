#!/usr/bin/env bash
set -e

echo "======================================"
echo "Running authentik devcontainer setup"
echo "======================================"

echo ""
echo "Step 1/5: Installing dependencies"
make install

echo ""
echo "Step 2/5: Generating development config"
make gen-dev-config

echo ""
echo "Step 3/5: Running database migrations"
make migrate

echo ""
echo "Step 4/5: Generating API clients"
make gen

echo ""
echo "Step 5/5: Building web assets"
make web

echo ""
echo "======================================"
echo "Setup complete!"
echo "======================================"
echo ""
echo "You can now run:"
echo "  - 'make run-server' to start the backend server"
echo "  - 'make run-worker' to start the worker (must be ran once after initial setup)"
echo "  - 'make web-watch' for live web development"
echo ""
