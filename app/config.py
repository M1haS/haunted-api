from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Haunted API"
    app_version: str = "0.4.2"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./haunted.db"
    secret_key: str = "change-me-in-production-seriously"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    rate_limit_per_minute: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
