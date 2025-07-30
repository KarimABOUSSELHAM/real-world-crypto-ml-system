use std::env;
#[derive(Clone)]
pub struct Config{
    pub psql_host: String,
    pub psql_port: u16,
    pub psql_db: String,
    pub psql_user: String,
    pub psql_password: String,
    pub psql_view_name: String,
    pub api_port: u16,
}

impl Config {
    pub fn from_env() -> Result<Self, String> {
        let psql_port_str = env::var("PSQL_PORT")
            .map_err(|_| "Failed to find psql_port environment variable".to_string())?;
        let api_port_str=env::var("PREDICTION_API_PORT")
            .map_err(|_| 
                "Failed to find prediction_api_port environment variable".to_string()
            )?;
        Ok(Self {
            psql_host: env::var("PSQL_HOST").map_err(|_|
            "Failed to find psql_host environment variable"
            .to_string())?,
            psql_port: psql_port_str.parse::<u16>()
            .map_err(|_| 
                "PSQL_PORT must be a valid u16 integer".to_string())?,
            psql_db: env::var("PSQL_DB").map_err(|_|
            "Failed to find psql_db environment variable"
            .to_string())?,
            psql_user: env::var("PSQL_USER").map_err(|_|
            "Failed to find psql_user environment variable"
            .to_string())?,
            psql_password: env::var("PSQL_PASSWORD").map_err(|_|
            "Failed to find psql_password environment variable"
            .to_string())?,
            psql_view_name: env::var("PSQL_VIEW_NAME").map_err(|_|
            "Failed to find psql_view_name environment variable"
            .to_string())?,
            api_port: api_port_str.parse::<u16>()
            .map_err(|_| 
                "api_port must be a valid u16 integer".to_string())?,
        })
    }
}
