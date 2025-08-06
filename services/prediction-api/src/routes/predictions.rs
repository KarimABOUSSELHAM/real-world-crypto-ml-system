use axum::{
    extract::
    {
        Query,
        State,
    }, Json
};
use serde::{
    Deserialize,
    Serialize,
};
use crate::AppState;
use log::info;

#[derive(Deserialize)]
pub struct PredictionParams {
    pair: String,

}

#[derive(Serialize, sqlx::FromRow)]
pub struct PredictionOutput {
    pair: String,
    predicted_price: f64,
    ts_ms: i64,
    predicted_ts_ms: i64,
}

pub async fn get_prediction(
    params: Query<PredictionParams>,
    State(app_state): State<AppState>
) -> Result<Json<PredictionOutput>, Json<PredictionOutput>> {
    let pair = &params.pair;
    info!("Requested prediction for {}", pair);
    let pool=app_state.pool;
    let psql_view=app_state.config.psql_view_name;
    // Refresh the materialized view before querying
    let refresh_query = format!("REFRESH MATERIALIZED VIEW CONCURRENTLY public.{}", psql_view);
    if let Err(e) = sqlx::query(&refresh_query).execute(&pool).await {
    eprintln!("Failed to refresh materialized view: {:?}", e);
    }
    let query=format!(
        "SELECT pair, predicted_price, ts_ms, predicted_ts_ms FROM public.{} WHERE pair = $1", 
        psql_view
    );
    let prediction_output = sqlx::query_as::<_, PredictionOutput>(&query)
        .bind(pair)
        .fetch_one(&pool).await
        .map_err(|e| {
            eprintln!("Database error: {:?}", e);
            Json(PredictionOutput {
                pair: pair.clone(),
                predicted_price: -1.0, // Sentinel value to show there is an error
                ts_ms: -1,
                predicted_ts_ms: -1,
            })
        })?;
        info!("Returning prediction");
    Ok(Json(prediction_output))
}
