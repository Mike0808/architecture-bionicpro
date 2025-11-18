-- Подключаемся к БД CRM
\c bionicpro_crm;

-- Таблицы CRM
CREATE TABLE customer (
    id VARCHAR(100) PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE product (
    id UUID PRIMARY KEY,
    model_name VARCHAR(100) NOT NULL,
    description TEXT,
    firmware_version VARCHAR(20) NOT NULL
);

CREATE TABLE "order" (
    id UUID PRIMARY KEY,
    customer_id VARCHAR(100) NOT NULL REFERENCES customer(id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES product(id),
    prosthesis_serial VARCHAR(50) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('paid', 'in_production', 'delivered', 'active')),
    delivered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);