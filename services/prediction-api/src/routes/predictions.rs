use axum::{
    extract::
    {
        Query,
        State,
    },
    Json,
};
use serde::{
    Deserialize,
    Serialize,
};
use crate::AppState;

#[derive(Deserialize)]
pub struct PredictionParams {
    pair: String,

}

#[derive(Serialize, sqlx::FromRow)]
pub struct PredictionOutput {
    pair: String,
    predicted_price: f64,
}

pub async fn get_prediction(
    params: Query<PredictionParams>,
    State(app_state): State<AppState>
) -> Result<Json<PredictionOutput>, Json<PredictionOutput>> {
    let pair = &params.pair;
    let pool=app_state.pool;
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
