#!/usr/bin/env bash
source $(dirname $0)/../.env.db

docker run --name yaktoto-postgres \
    -e POSTGRES_USER=$POSTGRES_USER \
    -e POSTGRES_PASSWORD=$POSTGRES_PASSWORD \
    -e POSTGRES_DB=$POSTGRES_DB \
    -p $POSTGRES_PORT:5432 \
    -d postgres:17.5-alpine3.22
