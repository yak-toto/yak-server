#!/bin/sh
set -e

echo "Create database schema"
yak db create

echo "Initialize database"
yak db init

echo "Creating admin user"
yak db admin --password $ADMIN_PASSWORD

echo "Container setup done!"

exec "$@"
