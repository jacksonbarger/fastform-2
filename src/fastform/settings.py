from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FastForm 2.0"
    host: str = "127.0.0.1"
    port: int = 8000

    # Database file path (can be overridden in tests or via env)
    db_path: str = "fastform.db"

    # External integrations / secrets
    openai_api_key: str | None = None
    fastform_api_token: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def openai_key_found(self) -> bool:
        return bool(self.openai_api_key)

    @property
    def auth_enabled(self) -> bool:
        return bool(self.fastform_api_token)


settings = Settings()
