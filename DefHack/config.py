from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    MINIO_ENDPOINT: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str = "intel"
    OPENAI_API_KEY: str
    EMBED_MODEL: str = "text-embedding-3-large"
    EMBED_DIM: int = 3072
    API_WRITE_KEY: str = "change-me"
    TELEGRAM_BOT_TOKEN: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()