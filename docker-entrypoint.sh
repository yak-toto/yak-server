#!/bin/sh
set -e

echo "Validating environment variables and settings"
python -c "
from yak_server.database.settings import PostgresSettings, RedisSettings
from yak_server.helpers.settings import Settings, AuthenticationSettings, CookieSettings

PostgresSettings()
RedisSettings()
Settings()
AuthenticationSettings()
CookieSettings()
"

echo "Create database schema"
yak db create

echo "Initialize database"
yak db init

echo "Creating admin user"
yak db admin --password $ADMIN_PASSWORD

echo "Container setup done!"

exec "$@"
