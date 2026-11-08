from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "AutoFlow"
    app_env: str = "development"
    secret_key: str = "development-only-change-me"
    database_url: str = "sqlite:///./autoflow.db"
    platform_admin_email: str | None = None
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @model_validator(mode="after")
    def validate_production_secrets(self):
        if self.app_env.lower() == "production":
            if self.secret_key == "development-only-change-me" or len(self.secret_key) < 32:
                raise ValueError("Production requires a unique SECRET_KEY with at least 32 characters")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production must use PostgreSQL, not SQLite")
        return self

settings = Settings()
