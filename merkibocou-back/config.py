from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8")

    jwt_secret_key: str  # Remplacez par une clé forte
    db_url: str

    cron_secret_key: str


settings = Settings()
