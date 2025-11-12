# --- Builder stage ---
FROM rust:1.89-slim-bullseye AS builder

RUN apt-get update && \
    apt-get install -y ca-certificates pkg-config cmake build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем манифесты
COPY Cargo.toml Cargo.lock ./

# Копируем исходники
COPY src ./src

# Собираем релизный бинарь
RUN cargo build --release --locked --bin report-service

# --- Runtime stage ---
FROM debian:bullseye-slim

RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -r -s /bin/false appuser

# Копируем только бинарь
COPY --from=builder /app/target/release/report-service /usr/local/bin/report-service
RUN chmod +x /usr/local/bin/report-service

USER appuser

ENV RUST_LOG=debug
EXPOSE 8000

CMD ["/usr/local/bin/report-service"]