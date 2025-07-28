use axum::{
    routing::get, 
    Router,
    extract::Query,
    response::IntoResponse,
};
use serde::Deserialize;
use sqlx::postgres::PgPoolOptions;
#[tokio::main]
async fn main() {
    // build our application with a route
    let app = Router::new()
        // `GET /` goes to `root`
        .route("/health", get(health))
        .route("/prediction", get(get_prediction));

    // run our app with hyper, listening globally on port 3001
    let listener = tokio::net::TcpListener::bind("0.0.0.0:3001").await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

// basic handler that responds with a static string
async fn health() -> &'static str {
    "I am healthy!!!!"
}

#[derive(Deserialize)]
struct PredictionParams {
    pair: String,

}
async fn get_prediction(params: Query<PredictionParams>) -> Result<impl IntoResponse, impl IntoResponse> {
    let pair = &params.pair;
    
    // Create a connection pool so that we can talk to risingwave database
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect("postgres://root:123@localhost:4567/dev")
        .await
        .map_err(
            |e| format!("Connection to risingwave failed: {}", e)
        )?;
    // Make a simple query to return the given parameter (use a question mark `?` instead of `$1` for MySQL/MariaDB)
    // let row: (i64,) = sqlx::query_as("SELECT $1")
    //     .bind(150_i64)
    //     .fetch_one(&pool).await
    //     .map_err(|e| format!("Query error {}", e))?;
    // assert_eq!(row.0, 150);
    #[derive(sqlx::FromRow)]
    struct PredictionOutput { pair: String, predicted_price: f64 }

    let prediction_output = sqlx::query_as::<_, PredictionOutput>(
        "SELECT pair, predicted_price FROM predictions WHERE pair = $1"
        )
        .bind(pair)
        .fetch_one(&pool).await.unwrap();
    let output= format!(
        "The price prediction for {} is {}", prediction_output.pair, prediction_output.predicted_price
    );
    Ok::<std::string::String, std::string::String>(output)
}
