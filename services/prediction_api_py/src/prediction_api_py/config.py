from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='services/prediction_api_py/.env.local',
        evn_file_encoding='utf-8',
    )

    prediction_api_port: int
    psql_view_name: str
    psql_table_name: str
    psql_host: str
    psql_port: int
    psql_db: str
    psql_user: str
    psql_password: str


config = Settings()
