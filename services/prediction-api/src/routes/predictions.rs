use axum::{
    extract::Query,
    Json,
};
use std::env;
use serde::{
    Deserialize,
    Serialize,
};
use sqlx::postgres::PgPoolOptions;

#[derive(Deserialize)]
pub struct PredictionParams {
    pair: String,

}

#[derive(Serialize, sqlx::FromRow)]
pub struct PredictionOutput {
    pair: String,
    predicted_price: f64,
}

pub async fn get_prediction(params: Query<PredictionParams>) -> Result<Json<PredictionOutput>, Json<PredictionOutput>> {
    let pair = &params.pair;
    let database_url=env::var("PREDICTION_DATABASE_URL")
    .map_err(|_e| {
            Json(PredictionOutput {
                pair: pair.clone(),
                predicted_price: -1.0, // Sentinel value to show there is an error
            })
        })?;
    // Create a connection pool so that we can talk to risingwave database
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .map_err(|_e| {
            Json(PredictionOutput {
                pair: pair.clone(),
                predicted_price: -1.0, // Sentinel value to show there is an error
            })
        })?;
    let prediction_output = sqlx::query_as::<_, PredictionOutput>(
        "SELECT pair, predicted_price FROM predictions WHERE pair = $1"
        )
        .bind(pair)
        .fetch_one(&pool).await
        .map_err(|_e| {
            Json(PredictionOutput {
                pair: pair.clone(),
                predicted_price: -1.0, // Sentinel value to show there is an error
            })
        })?;

    Ok(Json(prediction_output))
}
