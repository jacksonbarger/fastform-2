from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastForm 2.0"
    host: str = "127.0.0.1"
    port: int = 8000
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
