-- Создаём БД (если нужно)
CREATE DATABASE IF NOT EXISTS bionicpro;

-- Создаём витрину
CREATE TABLE IF NOT EXISTS bionicpro.report_datamart (
    customer_id String,
    prosthesis_serial String,
    report_date Date,
    total_gestures UInt32,
    avg_response_time_ms Float32,
    min_battery_level UInt8,
    max_battery_level UInt8,
    error_count UInt16,
    active_hours UInt8
)
ENGINE = MergeTree()
ORDER BY (customer_id, report_date);