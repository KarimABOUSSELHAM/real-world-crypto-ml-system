from pydantic_settings import BaseSettings, SettingsConfigDict


class CryptopanicConfig(BaseSettings):
    """
    Configuration of the cryptopanic API.
    """

    cryptopanic_api_key: str
    model_config = SettingsConfigDict(
        env_file='src/news/cryptopanic_credentials.env',
        env_file_encoding='utf-8',
    )


cryptopanic_config = CryptopanicConfig()
