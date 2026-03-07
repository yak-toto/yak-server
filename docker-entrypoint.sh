#!/bin/sh
set -e

echo "Create database schema"
yak db create

echo "Initialize database"
yak db init

echo "Creating admin user"
yak db admin --password $ADMIN_PASSWORD

echo "Validating environment variables and settings"
python -c "
from yak_server.database.settings import PostgresSettings
from yak_server.helpers.settings import Settings, AuthenticationSettings, CookieSettings

PostgresSettings()
Settings()
AuthenticationSettings()
CookieSettings()
"

echo "Container setup done!"

exec "$@"
