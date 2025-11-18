use crate::ReportRow;
use clickhouse::Client;
use uuid::Uuid;

#[derive(Clone)]
pub struct ReportRepository {
    client: Client,
}

impl ReportRepository {
    pub fn new(client: Client) -> Self {
        Self { client }
    }

    pub async fn find_by_customer(
        &self,
        customer_id: &String,
    ) -> Result<Vec<ReportRow>, clickhouse::error::Error> {
        let mut cursor = self
            .client
            .query(
                "SELECT 
                        customer_id,
                        prosthesis_serial,
                        report_date,
                        total_gestures,
                        avg_response_time_ms,
                        min_battery_level,
                        max_battery_level,
                        error_count,
                        active_hours
                    FROM bionicpro.report_datamart
                    WHERE customer_id = ?",
            )
            .bind(customer_id)
            .fetch::<ReportRow>()
            .unwrap();

        let mut results = Vec::new();
        while let Some(row) = cursor.next().await? {
            results.push(row);
        }

        Ok(results)
    }
}
