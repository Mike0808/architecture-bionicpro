mod repository;
use crate::repository::ReportRepository;
use axum::{
    Router,
    extract::State,
    http::{HeaderValue, Method, StatusCode, header},
    response::Json,
    routing::get,
    serve,
};
use chrono::NaiveDate;
use jwt_authorizer::{IntoLayer, JwtAuthorizer, JwtClaims, Validation};
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tokio::net::TcpListener;
use tower_http::cors::{AllowOrigin, CorsLayer};
use tracing_subscriber::{EnvFilter, fmt, util::SubscriberInitExt};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, clickhouse::Row)]
struct ReportRow {
    #[serde(rename = "customer_id")]
    customer_id: String,
    prosthesis_serial: String,
    report_date: NaiveDate,
    total_gestures: u32,
    avg_response_time_ms: f32,
    min_battery_level: u8,
    max_battery_level: u8,
    error_count: u16,
    active_hours: u8,
}

#[derive(Debug, Serialize)]
struct ReportResponse {
    customer_id: Uuid,
    reports: Vec<ReportRow>,
}
// === Кастомный extractor на основе JwtClaims ===

#[derive(Debug, Deserialize, Serialize, Clone)]
struct KeycloakClaims {
    sub: String, // Keycloak возвращает sub как строку (обычно UUID)
                 // Дополнительно можно добавить: email, preferred_username и т.д.
}

#[derive(Clone)]
struct AppState {
    repository: ReportRepository,
}

async fn get_reports(
    JwtClaims(custom, ..): JwtClaims<KeycloakClaims>,
    State(state): State<AppState>,
) -> Result<Json<ReportResponse>, (StatusCode, String)> {
    tracing::trace!(?custom, "✅ JWT claims successfully extracted");

    //let customer_id = Uuid::parse_str(&custom.sub).map_err(|e| {
    //    tracing::warn!("Invalid customer_id in token: {}", e);
    //    (
    //        StatusCode::BAD_REQUEST,
    //        "Некорректный customer_id в токене".to_string(),
    //    )
    //})?;
    let customer_id = &custom.sub;
    tracing::info!(%customer_id, "🔍 Fetching reports from ClickHouse");
    let reports = state
        .repository
        .find_by_customer(customer_id)
        .await
        .map_err(|e| {
            tracing::error!("Failed to fetch reports from ClickHouse: {}", e);
            (
                StatusCode::INTERNAL_SERVER_ERROR,
                "Database error".to_string(),
            )
        })?;

    tracing::info!(%customer_id, count = reports.len(), "✅ Returning reports");
    let customer_uuid = Uuid::parse_str(customer_id).unwrap();
    Ok(Json(ReportResponse {
        customer_id: customer_uuid,
        reports,
    }))
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Включаем TRACE для всех компонентов
    fmt()
        .with_env_filter(EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            "report_service=trace,axum=trace,jwt_authorizer=trace,clickhouse=trace".into()
        }))
        .finish()
        .init();
    // Конфигурация из env
    let keycloak_issuer_url = std::env::var("KEYCLOAK_ISSUER_URL")
        .unwrap_or_else(|_| "http://localhost:8080/realms/myrealm".to_string());
    let client_id = std::env::var("CLIENT_ID").unwrap_or_else(|_| "report-service".to_string());
    let server_addr = std::env::var("SERVER_ADDR").unwrap_or_else(|_| "127.0.0.1:8000".to_string());
    let clickhouse_user =
        std::env::var("CLICKHOUSE_USER").unwrap_or_else(|_| "default".to_string());
    let clickhouse_password =
        std::env::var("CLICKHOUSE_PASSWORD").unwrap_or_else(|_| "".to_string());

    let frontend_addr =
        std::env::var("FRONTEND_ADDR").unwrap_or_else(|_| "127.0.0.1:3000".to_string());
    // Инициализация ClickHouse
    let clickhouse_url =
        std::env::var("CLICKHOUSE_URL").unwrap_or_else(|_| "http://localhost:8123".to_string());
    let clickhouse_db = std::env::var("CLICKHOUSE_DB").unwrap_or_else(|_| "default".to_string());

    let clickhouse_client = clickhouse::Client::default()
        .with_url(&clickhouse_url)
        .with_database(&clickhouse_db)
        .with_user(&clickhouse_user) // ← добавлено
        .with_password(&clickhouse_password); // ← добавлено
    let repository = ReportRepository::new(clickhouse_client);
    let app_state = AppState { repository };

    // Настройка валидации JWT: issuer + audience = client_id
    let validation = Validation::new()
        // .iss(&[&keycloak_issuer_url]) // можно опустить, если не нужно
        .aud(&[&client_id]);

    // Настройка JWT авторизации через Keycloak OIDC
    let authorizer = JwtAuthorizer::<KeycloakClaims>::from_oidc(&keycloak_issuer_url)
        .validation(validation)
        .build()
        .await?;
    let cors = CorsLayer::new()
        .allow_origin(AllowOrigin::exact(
            HeaderValue::from_str(&frontend_addr).expect("Invalid origin header value"),
        ))
        .allow_methods([Method::GET, Method::OPTIONS])
        .allow_headers([header::AUTHORIZATION, header::CONTENT_TYPE])
        .allow_credentials(true); // ✅ Теперь безопасно

    let app = Router::new()
        .route("/reports", get(get_reports))
        .with_state(app_state)
        .layer(authorizer.into_layer())
        .layer(cors);

    let addr: SocketAddr = server_addr.parse()?;
    tracing::info!("Binding to address: {}", addr);
    let listener = TcpListener::bind(addr).await?;
    tracing::info!("✅ Successfully bound to TCP socket");

    tracing::info!("🚀 Starting HTTP server on http://{}", addr);

    serve(listener, app).await?;
    Ok(())
}
