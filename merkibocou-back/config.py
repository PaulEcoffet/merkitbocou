from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding="utf-8")

    # Clés JWT et DB
    jwt_secret_key: str
    cron_secret_key: str
    db_url: str

    # Configuration des e-mails
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_from_name: str
    mail_starttls: bool
    mail_ssl_tls: bool
    mail_validate_certs: bool


settings = Settings()