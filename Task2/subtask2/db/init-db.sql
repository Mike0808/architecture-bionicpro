-- Подключаемся к БД телеметрии
\connect bionicpro_telemetry;

-- Таблица телеметрии
CREATE TABLE telemetry_raw (
    id SERIAL PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL,
    prosthesis_serial VARCHAR(50) NOT NULL,
    event_time TIMESTAMP NOT NULL DEFAULT NOW(),
    emg_signal_magnitude FLOAT CHECK (emg_signal_magnitude >= 0),
    response_time_ms INT CHECK (response_time_ms BETWEEN 0 AND 1000),
    battery_level_percent INT CHECK (battery_level_percent BETWEEN 0 AND 100),
    actuator_position_degrees FLOAT,
    error_code VARCHAR(10),
    gesture_type VARCHAR(30)
);

-- Индекс для ускорения запросов по дате и пользователю
CREATE INDEX idx_telemetry_customer_time ON telemetry_raw (customer_id, event_time);