use axum::{
    routing::get, 
    Router,
};
use std::io;
mod routes;
use log::info;
mod db;
mod config;
use config::Config;
use routes::health::health;
use routes::predictions::get_prediction;
use sqlx::PgPool;

#[derive(Clone)]
struct AppState {
    pool:  PgPool,
    config: Config,
}
#[tokio::main]
async fn main() -> Result<(), std::io::Error>{
    // Start the logger as early as possible 
    env_logger::init();
    // Loading env variables into config struct
    let config=Config::from_env()
    .map_err(|e| io::Error::new(io::ErrorKind::Other, 
        format!("Failed to load the config: {}", e)))?;
    // Creating a single PgPool at start up
    info!("Creating pg pool...");
    let pool=match db::get_pool(
        &config.psql_host,
        &config.psql_port,
        &config.psql_db,
        &config.psql_user,
        &config.psql_password,
    ).await {
        Ok(pool) => pool,
        Err(e) => {
            eprintln!("Error found while creating DB {}", e);
            std::process::exit(1);
        }
    };
    info!("Created pg pool successfully");
    
    // Creating the state struct
    let app_state= AppState {
        pool,
        config: config.clone(),
    };
    // build our application with a route
    let app = Router::new()
        // `GET /` goes to `root`
        .route("/health", get(health))
        .route("/prediction", get(get_prediction))
        .with_state(app_state);

    // run our app with hyper, listening globally on port 3001
    let listener = tokio::net::TcpListener::bind(
        format!("0.0.0.0:{}", config.api_port)
    )
    .await?;
    axum::serve(listener, app).await?;

    Ok(())
}


