#!/bin/bash

echo "Starting Vercel Build..."

# No pip install here (Vercel Dashboard handles this)

# Run migrations
python3 manage.py migrate --noinput

# Run collectstatic
python3 manage.py collectstatic --noinput --clear

echo "Vercel Build Finished!"
