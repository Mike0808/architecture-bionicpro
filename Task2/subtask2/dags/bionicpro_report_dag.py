"""
ETL DAG: агрегация данных из CRM и Telemetry → витрина в ClickHouse.
Запускается ЕЖЕДНЕВНО.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
from clickhouse_driver import Client
import logging
from config import CRM_DB, TELEMETRY_DB, CLICKHOUSE


def extract_and_load_report_datamart(**context):
    execution_date = context['execution_date']
    report_date = (execution_date - timedelta(days=1)).date()
    logging.info(f"📊 Generating report for {report_date}")

    # === 1. Получаем данные из Telemetry за вчерашний день ===
    telemetry_conn = psycopg2.connect(**TELEMETRY_DB)
    telemetry_cur = telemetry_conn.cursor()

    telemetry_cur.execute("""
        SELECT
            customer_id,
            prosthesis_serial,
            COUNT(*) AS total_gestures,
            AVG(response_time_ms) AS avg_response_time_ms,
            MIN(battery_level_percent) AS min_battery_level,
            MAX(battery_level_percent) AS max_battery_level,
            COUNT(error_code) FILTER (WHERE error_code IS NOT NULL) AS error_count,
            COUNT(DISTINCT DATE_TRUNC('hour', event_time)) AS active_hours
        FROM telemetry_raw
        WHERE event_time >= %s AND event_time < %s
        GROUP BY customer_id, prosthesis_serial
    """, (report_date, report_date + timedelta(days=1)))

    rows = telemetry_cur.fetchall()
    telemetry_cur.close()
    telemetry_conn.close()

    if not rows:
        logging.info("⚠️ No telemetry data for this date")
        return

    # === 2. Дополняем данными из CRM (если нужно) ===
    # В данном случае агрегация по customer_id уже есть, но можно добавить проверку активности протеза
    crm_conn = psycopg2.connect(**CRM_DB)
    crm_cur = crm_conn.cursor()

    valid_prostheses = set()
    crm_cur.execute("""
        SELECT prosthesis_serial
        FROM "order"
        WHERE status = 'active'
    """)
    for (serial,) in crm_cur.fetchall():
        valid_prostheses.add(serial)

    crm_cur.close()
    crm_conn.close()

    # Фильтруем только активные протезы
    filtered_rows = [
        row for row in rows
        if row[1] in valid_prostheses  # row[1] = prosthesis_serial
    ]

    if not filtered_rows:
        logging.info("⚠️ No active prostheses found for telemetry data")
        return

    # === 3. Загрузка в ClickHouse ===
    ch_client = Client(**CLICKHOUSE)

    # Удаляем старые данные за дату (идемпотентность)
    ch_client.execute(
        f"ALTER TABLE bionicpro.report_datamart DELETE WHERE report_date = '{report_date}'"
    )

    # Вставка
    ch_client.execute(
        """
        INSERT INTO bionicpro.report_datamart (
            customer_id, prosthesis_serial, report_date,
            total_gestures, avg_response_time_ms,
            min_battery_level, max_battery_level,
            error_count, active_hours
        ) VALUES
        """,
        [
            (
                row[0], row[1], str(report_date),
                int(row[2]), float(row[3]),
                int(row[4]), int(row[5]),
                int(row[6]), int(row[7])
            )
            for row in filtered_rows
        ]
    )
    logging.info(f"✅ Inserted {len(filtered_rows)} report records")


# === DAG ===
with DAG(
    dag_id='bionicpro_report_datamart',
    description='ETL: CRM + Telemetry → ClickHouse Report Mart',
    schedule_interval='0 2 * * *',  # ежедневно в 02:00 UTC
    start_date=datetime(2025, 11, 1),
    catchup=False,
    tags=['bionicpro', 'etl', 'reporting']
) as dag:

    etl_task = PythonOperator(
        task_id='extract_and_load_report_datamart',
        python_callable=extract_and_load_report_datamart,
        provide_context=True
    )