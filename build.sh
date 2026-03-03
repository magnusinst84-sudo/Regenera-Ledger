#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Regenera Ledger — Single-Service Build Script for Render
# 1. Builds the React frontend (output: frontend/dist/)
# 2. Installs Python backend dependencies
# ─────────────────────────────────────────────────────────────
set -e  # Exit immediately if any command fails

echo "==> [1/2] Building React frontend..."
cd frontend
npm install
# VITE_API_URL is empty intentionally — frontend and backend share the same origin
VITE_API_URL="" npm run build
cd ..

echo "==> [2/2] Installing Python backend dependencies..."
cd backend
pip install -r requirements.txt
cd ..

echo "==> Build complete!"
