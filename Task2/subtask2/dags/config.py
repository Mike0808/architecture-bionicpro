# dags/config.py

# PostgreSQL: CRM
CRM_DB = {
    'host': 'postgres',
    'port': 5432,
    'database': 'bionicpro_crm',
    'user': 'airflow',
    'password': 'airflow'
}

# PostgreSQL: Telemetry
TELEMETRY_DB = {
    'host': 'postgres',
    'port': 5432,
    'database': 'bionicpro_telemetry',
    'user': 'airflow',
    'password': 'airflow'
}

# ClickHouse: витрина отчётов
CLICKHOUSE = {
    'host': 'clickhouse',
    'port': 9000,
    'database': 'bionicpro',
    'user': 'airflow',
    'password': 'airflow'
}