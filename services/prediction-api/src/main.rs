use axum::{
    routing::get, 
    Router,
};
use std::env;
mod routes;
mod db;
use routes::health::health;
use routes::predictions::get_prediction;
use sqlx::PgPool;

#[derive(Clone)]
struct AppState {
    pool:  PgPool,
}
#[tokio::main]
async fn main() -> Result<(), std::io::Error>{
    // Creating a single PgPool at start up
    let pool=match db::get_pool().await {
        Ok(pool) => pool,
        Err(e) => {
            eprintln!("Error found while creating DB {}", e);
            std::process::exit(1);
        }
    };
    // Creating the state struct
    let app_state= AppState {
        pool
    };
    // build our application with a route
    let app = Router::new()
        // `GET /` goes to `root`
        .route("/health", get(health))
        .route("/prediction", get(get_prediction))
        .with_state(app_state);

    // run our app with hyper, listening globally on port 3001
    let port=env::var("PORT").unwrap_or("3001".to_string());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{}", port))
    .await?;
    axum::serve(listener, app).await?;

    Ok(())
}


