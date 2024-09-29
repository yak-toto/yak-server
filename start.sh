#!/bin/sh

# Wait for MySQL to be available on port 3306
# /app/wait-for-it.sh db:3306 --timeout=60 --strict -- echo "MySQL is up - executing command"

# Run your setup commands here, e.g., migrations or database seeding
echo "Running database migrations..."
yak env init

yak db create
yak db init

# Start FastAPI using Uvicorn
echo "Starting FastAPI..."
uvicorn --factory --host 0.0.0.0 --port 8000 yak_server:create_app
