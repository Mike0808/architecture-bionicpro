# Report Service — Secure API for User Usage Reports

![Rust](https://img.shields.io/badge/Rust-1.89+-black?logo=rust)
![Axum](https://img.shields.io/badge/Axum-0.7-blue)
![ClickHouse](https://img.shields.io/badge/ClickHouse-22+-green)
![Keycloak](https://img.shields.io/badge/Keycloak-22+-orange)

**Report Service** — это высокопроизводительный микросервис на Rust, который предоставляет персонализированные отчёты об использовании протеза для авторизованных пользователей. Сервис интегрируется с Keycloak для аутентификации и авторизации, а данные хранятся и агрегируются в OLAP-системе ClickHouse.

---

## 📌 Основные возможности

- 🔐 **Безопасная аутентификация** через Keycloak с использованием PKCE flow
- 🛡️ **JWT-валидация** с автоматической загрузкой JWKS и проверкой подписи
- ⚡ **Высокая производительность** благодаря использованию ClickHouse для аналитических запросов
- 📊 **Готовые отчёты** по использованию: жесты, время отклика, уровень батареи, ошибки
- 🐳 **Готов к работе в Docker** с минимальным footprint'ом и поддержкой non-root запуска
- 📝 **Полное логирование** с поддержкой уровней через `RUST_LOG`

---

## 🗂️ Структура данных

Отчёт формируется на основе таблицы `report_datamart` в ClickHouse:

| Поле | Тип | Описание |
|------|-----|----------|
| `customer_id` | UUID | Идентификатор пользователя (совпадает с `sub` из Keycloak) |
| `prosthesis_serial` | String | Серийный номер протеза |
| `report_date` | Date | Дата агрегации отчёта |
| `total_gestures` | UInt32 | Общее количество распознанных жестов |
| `avg_response_time_ms` | Float32 | Среднее время отклика (мс) |
| `min_battery_level` | UInt8 | Минимальный уровень заряда (%) |
| `max_battery_level` | UInt8 | Максимальный уровень заряда (%) |
| `error_count` | UInt16 | Количество ошибок |
| `active_hours` | UInt8 | Часы активного использования |

---

## 🚀 Быстрый старт

### Требования

- Docker 20.10+
- Docker Compose (опционально)
- Keycloak 22+ (настроенный realm)
- ClickHouse 22+ (с таблицей `report_datamart`)

### 1. Настройка переменных окружения

Создайте файл `.env`:

```env
# Keycloak
KEYCLOAK_ISSUER_URL=http://localhost:8080/realms/myrealm
CLIENT_ID=report-service

# ClickHouse
CLICKHOUSE_URL=http://clickhouse:8123
CLICKHOUSE_DB=default
CLICKHOUSE_USER=airflow
CLICKHOUSE_PASSWORD=your_secure_password

# Сервер
SERVER_ADDR=0.0.0.0:3001
RUST_LOG=info
```

### 2. Сборка и запуск

```bash
# Сборка образа
docker build -t report-service .

# Запуск
docker run -d \
  --name report-service \
  --env-file .env \
  -p 3001:3001 \
  report-service
```

Или через Docker Compose (пример `docker-compose.yml` ниже).

### 3. Использование

Отправьте GET-запрос с валидным JWT-токеном:

```bash
curl -H "Authorization: Bearer <ваш_access_token>" \
     -H "Content-Type: application/json" \
     http://localhost:3001/reports
```

Пример ответа:

```json
{
  "customer_id": "7e29f397-6679-4e18-8426-18b0b3078fca",
  "reports": [
    {
      "customer_id": "7e29f397-6679-4e18-8426-18b0b3078fca",
      "prosthesis_serial": "PROS-12345",
      "report_date": "2025-11-12",
      "total_gestures": 150,
      "avg_response_time_ms": 45.6,
      "min_battery_level": 20,
      "max_battery_level": 100,
      "error_count": 2,
      "active_hours": 6
    }
  ]
}
```

---

## 🧩 Фронтенд-интеграция

Для скачивания отчёта из React-приложения с использованием `@react-keycloak/web`:

```ts
const downloadReport = async () => {
  await keycloak.updateToken(30);
  const response = await fetch(`${API_URL}/reports`, {
    headers: {
      'Authorization': `Bearer ${keycloak.token}`,
      'Content-Type': 'application/json'
    }
  });
  const data = await response.json();
  // ... инициировать скачивание
};
```

> 💡 Сервис автоматически извлекает `customer_id` из поля `sub` JWT-токена.

---

## 📦 Архитектура

```
Frontend (React + Keycloak)
        │
        ↓ (PKCE flow)
    Keycloak (OIDC Provider)
        │
        ↓ (access_token)
Report Service (Rust + Axum)
        │
        ↓ (customer_id = sub)
    ClickHouse (OLAP)
```

---

## 🔐 Безопасность

- Все запросы защищены JWT-токенами
- Проверка подписи через JWKS
- Валидация `issuer` и `audience`
- Non-root пользователь в Docker
- Поддержка TLS (через `rustls`)

---

## 🛠 Разработка

### Локальная сборка

```bash
cargo build --release
./target/release/report-service
```

### Требуемые зависимости

- `libssl-dev` (только для локальной сборки с `vendored` OpenSSL)
- Rust 1.89+

### Логирование

Уровень логирования управляется через `RUST_LOG`:

```bash
RUST_LOG=debug cargo run
```

---

## 📄 Лицензия

Этот проект распространяется под лицензией MIT. Подробнее см. в файле [LICENSE](LICENSE).

---

## 🙌 Благодарности

- [Axum](https://github.com/tokio-rs/axum) — веб-фреймворк для Rust
- [clickhouse-rs](https://github.com/akumuli/clickhouse-rs) — клиент ClickHouse
- [jwt-authorizer](https://github.com/borshchok/jwt-authorizer) — JWT-валидация для Axum
- [Keycloak](https://www.keycloak.org/) — identity и access management

---

> 📬 Вопросы и предложения: откройте Issue или отправьте PR!