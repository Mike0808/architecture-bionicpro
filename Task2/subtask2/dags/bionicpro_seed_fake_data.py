"""
DAG для генерации тестовых данных в CRM и Telemetry.
Запускается ВРУЧНУЮ. Идемпотентен.
"""

from datetime import datetime, timedelta
import uuid
import random
import logging
from airflow import DAG
from airflow.operators.python import PythonOperator
import psycopg2
from config import CRM_DB, TELEMETRY_DB


def seed_fake_data(**context):
    logging.info("🚀 Starting fake data seeding...")

    # === 1. Подключение к CRM и Telemetry ===
    crm_conn = psycopg2.connect(**CRM_DB)
    telemetry_conn = psycopg2.connect(**TELEMETRY_DB)
    crm_cur = crm_conn.cursor()
    telemetry_cur = telemetry_conn.cursor()

    try:
        # === 2. Проверка: есть ли данные? ===
        crm_cur.execute("SELECT COUNT(*) FROM customer")
        if crm_cur.fetchone()[0] > 0:
            logging.info("✅ Fake data already exists → skipping.")
            return

        # === 3. Генерация пользователей и продуктов ===
        logging.info("🌱 Generating CRM data...")

        first_names = ["Алексей", "Мария", "Иван", "Екатерина", "Дмитрий"]
        last_names = ["Смирнов", "Иванова", "Кузнецов", "Попова", "Соколов"]
        customers = []
        # uids_list = [
        #     uuid.UUID('7e29f397-6679-4e18-8426-18b0b3078fca'),
        #     uuid.UUID('d3c843cf-df4d-44be-81f8-737456a78c25'),
        #     uuid.UUID('ecb1d393-3aab-407e-9967-0df834531aa3'),
        #     uuid.UUID('14096a7c-909a-4590-98e8-97b9070c0725'),
        #     uuid.UUID('ef28f14b-cfa8-4ece-95f0-02fa55cc3117'),
        #     uuid.UUID('27adcf90-b5be-4257-a3d0-f420e7ae9706')
        # ]
        uids_list = [
            '7e29f397-6679-4e18-8426-18b0b3078fca',
            'd3c843cf-df4d-44be-81f8-737456a78c25',
            'ecb1d393-3aab-407e-9967-0df834531aa3',
            '14096a7c-909a-4590-98e8-97b9070c0725',
            'ef28f14b-cfa8-4ece-95f0-02fa55cc3117',
            '27adcf90-b5be-4257-a3d0-f420e7ae9706'
        ]
        for i in range(6):
            cid = uids_list[i]
            customers.append(cid)
            crm_cur.execute("""
                INSERT INTO customer (id, first_name, last_name, email, phone)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                cid,
                random.choice(first_names),
                random.choice(last_names),
                f"user{i}@bionicpro.test",
                f"+7900{random.randint(1000000, 9999999)}"
            ))

        hand_id = uuid.uuid4()
        leg_id = uuid.uuid4()
        crm_cur.execute("INSERT INTO product (id, model_name, firmware_version) VALUES (%s, %s, %s)",
                        (hand_id, "BionicPRO Hand v3", "3.1.2"))
        crm_cur.execute("INSERT INTO product (id, model_name, firmware_version) VALUES (%s, %s, %s)",
                        (leg_id, "BionicPRO Leg v2", "2.0.5"))

        # === 4. Заказы (в CRM) и телеметрия (в Telemetry) ===
        logging.info("📡 Generating telemetry data...")

        gestures = ["GRASP", "POINT", "OPEN", "REST"]
        errors = [None, None, None, "BAT_LOW", "NO_SIGNAL"]

        for i, cid in enumerate(customers):
            pid = hand_id if i % 2 == 0 else leg_id
            serial = f"BP-{random.randint(10000, 99999)}"

            # Заказ в CRM
            crm_cur.execute("""
                INSERT INTO "order" (id, customer_id, product_id, prosthesis_serial, status, delivered_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                uuid.uuid4(),
                cid,
                pid,
                serial,
                "active",
                datetime.now() - timedelta(days=random.randint(10, 100))
            ))

            # Телеметрия — последние 7 дней
            start_date = datetime.now() - timedelta(days=7)
            for day in range(7):
                for _ in range(20):  # ~20 событий в день
                    event_time = start_date + timedelta(
                        days=day,
                        hours=random.randint(8, 22),
                        minutes=random.randint(0, 59)
                    )
                    telemetry_cur.execute("""
                        INSERT INTO telemetry_raw (
                            customer_id, prosthesis_serial, event_time,
                            emg_signal_magnitude, response_time_ms,
                            battery_level_percent, gesture_type, error_code
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        cid,
                        serial,
                        event_time,
                        round(random.uniform(0.1, 1.8), 2),
                        random.randint(50, 180),
                        random.randint(10, 100),
                        random.choice(gestures),
                        random.choice(errors)
                    ))

        # Сохраняем всё
        crm_conn.commit()
        telemetry_conn.commit()
        logging.info("✅ Fake data seeded successfully!")

    except Exception as e:
        crm_conn.rollback()
        telemetry_conn.rollback()
        logging.error(f"❌ Error: {e}")
        raise
    finally:
        crm_cur.close()
        telemetry_cur.close()
        crm_conn.close()
        telemetry_conn.close()


# === DAG ===
with DAG(
    dag_id='bionicpro_seed_fake_data',
    description='Генерация тестовых данных для CRM и телеметрии',
    schedule_interval=None,  # только вручную
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=['bionicpro', 'fake-data', 'dev-only']
) as dag:

    seed_task = PythonOperator(
        task_id='seed_fake_data',
        python_callable=seed_fake_data,
        provide_context=True
    )