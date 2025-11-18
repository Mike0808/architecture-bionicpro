#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE bionicpro_crm;
    CREATE DATABASE bionicpro_telemetry;
    GRANT ALL PRIVILEGES ON DATABASE bionicpro_crm TO airflow;
    GRANT ALL PRIVILEGES ON DATABASE bionicpro_telemetry TO airflow;
EOSQL

# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init-crm.sql
# psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f /docker-entrypoint-initdb.d/init-db.sql