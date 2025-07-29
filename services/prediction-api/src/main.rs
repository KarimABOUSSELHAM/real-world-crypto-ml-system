use axum::{
    routing::get, 
    Router,
};
mod routes;
use routes::health::health;
use routes::predictions::get_prediction;
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


