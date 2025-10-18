#!/usr/bin/env bash

set -e

# Start PostgreSQL using docker compose (env_file handles .env.db automatically)
docker compose -f $(dirname $0)/../docker-compose.dev.yml up -d postgres

echo "PostgreSQL is starting..."
echo "Use 'docker compose -f docker-compose.dev.yml logs -f postgres' to see logs"
echo "Use 'docker compose -f docker-compose.dev.yml down' to stop"
