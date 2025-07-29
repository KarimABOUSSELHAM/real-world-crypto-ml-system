use axum::{
    routing::get, 
    Router,
};
use std::env;
mod routes;
use routes::health::health;
use routes::predictions::get_prediction;
#[tokio::main]
async fn main() -> Result<(), std::io::Error>{
    // build our application with a route
    let app = Router::new()
        // `GET /` goes to `root`
        .route("/health", get(health))
        .route("/prediction", get(get_prediction));

    // run our app with hyper, listening globally on port 3001
    let port=env::var("PORT").unwrap_or("3001".to_string());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port))
    .await?;
    axum::serve(listener, app).await?;

    Ok(())
}


