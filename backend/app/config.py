"""应用配置。所有值可用环境变量或 .env 覆盖。"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "CyberRange"
    api_prefix: str = "/api"

    secret_key: str = "cyberrange-dev-secret-key-please-change-in-production-0001"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 天

    # 本地默认 SQLite，零配置可跑；生产切 PostgreSQL
    database_url: str = "sqlite:///./cyberrange.db"

    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
