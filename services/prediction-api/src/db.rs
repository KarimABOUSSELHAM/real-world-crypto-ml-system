use sqlx::
{postgres::PgPoolOptions,
    PgPool,
};
use serde::{
    Serialize,
};

#[derive(Serialize, sqlx::FromRow)]
pub struct PredictionOutput {
    pair: String,
    predicted_price: f64,
}

pub async fn get_pool(
    psql_host: &String,
    psql_port: &u16,
    psql_db: &String,
    psql_user: &String,
    psql_password: &String,
) -> Result<PgPool,String> {
    let database_url=format!(
        "postgres://{}:{}@{}:{}/{}", psql_user, psql_password,
        psql_host, psql_port, psql_db
    );
    let pool = PgPoolOptions::new()
        .max_connections(5)
        .connect(&database_url)
        .await
        .map_err(|_e|
            "Failed to connect the pool to the database"
            .to_string())?;
    Ok(pool)
}