#!/bin/bash
set -e

echo "==> Building Rwanda Crime Report System"
echo "==> Current directory: $(pwd)"

cd backend
echo "==> Changed to backend directory: $(pwd)"

echo "==> Installing dependencies..."
pip install -r requirements.txt

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Build complete!"
