use sqlx::
{postgres::PgPoolOptions,
    PgPool,
}
    ;
use std::env;
use serde::{
    Serialize,
};

#[derive(Serialize, sqlx::FromRow)]
pub struct PredictionOutput {
    pair: String,
    predicted_price: f64,
}

pub async fn get_pool() -> Result<PgPool,String> {
    // let pair = &params.pair;
    let database_url=env::var("PREDICTION_DATABASE_URL")
    .map_err(|_e|
        "Failed to read PREDICTION_DATABASE_URL environment variable"
        .to_string())?;
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .map_err(|_e|
            "Failed to connect the pool to PREDICTION_DATABASE_URL environment variable"
            .to_string())?;
    Ok(pool)
}