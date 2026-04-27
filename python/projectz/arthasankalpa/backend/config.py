"""
config.py - Central settings using pydantic-settings.
All values load from backend/.env
"""
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Always look for .env next to THIS file (backend/.env)
# regardless of which directory the script is run from.
_ENV_FILE = Path(__file__).parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),        # absolute path -> no CWD-dependency
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o"
    openai_embed_model: str = "text-embedding-3-small"
    openai_embed_dims: int = 1536

    # Pinecone
    pinecone_api_key: str
    pinecone_index_name: str = "mf-advisor-india"
    pinecone_namespace: str = "funds"

    # Local services (Docker)
    redis_url: str = "redis://localhost:6379"
    database_url: str = "postgresql+asyncpg://mf_user:mf_secret_local@localhost:5432/mf_advisor"

    # App
    app_env: str = "development"
    secret_key: str = "local-dev-secret"
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Data sources
    amfi_nav_url: str = "https://portal.amfiindia.com/spages/NAVAll.txt"

    # RAG tuning
    retrieval_top_k: int = 20
    rerank_top_n: int = 5
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Cache TTLs (seconds)
    nav_cache_ttl: int = 14400       # 4 hours
    fund_meta_cache_ttl: int = 86400 # 24 hours
    recs_cache_ttl: int = 3600       # 1 hour

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    @property
    def is_dev(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    return Settings()