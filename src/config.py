from typing import Optional, Literal
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator
from pathlib import Path


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Server Configuration
    mcp_server_host: str = Field(default="localhost", description="MCP server host")
    mcp_server_port: int = Field(default=8000, description="MCP server port")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level"
    )

    # API Configuration
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    api_rate_limit: int = Field(default=100, description="API rate limit")
    api_rate_limit_period: int = Field(
        default=60, description="API rate limit period in seconds"
    )
    api_keys: Optional[str] = Field(
        default=None, description="Comma-separated list of valid API keys"
    )

    # Authentication
    jwt_secret_key: str = Field(
        default="change-this-in-production", description="JWT secret key"
    )
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiration_minutes: int = Field(
        default=30, description="JWT expiration in minutes"
    )

    # Vector Database Configuration
    chroma_persist_directory: Path = Field(
        default=Path("./data/chroma"), description="ChromaDB persist directory"
    )
    chroma_collection_name: str = Field(
        default="mcp_documents", description="ChromaDB collection name"
    )
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence transformer model"
    )

    # LLM API Keys
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    anthropic_api_key: Optional[str] = Field(
        default=None, description="Anthropic API key"
    )

    # LLM Configuration
    default_llm_provider: Literal["openai", "anthropic"] = Field(
        default="openai", description="Default LLM provider"
    )
    default_model: str = Field(
        default="gpt-4-turbo-preview", description="Default LLM model"
    )
    max_tokens: int = Field(default=4000, description="Maximum tokens for LLM")
    temperature: float = Field(default=0.7, description="LLM temperature")

    # Database
    database_url: str = Field(
        default="sqlite:///./data/mcp.db", description="Database URL"
    )

    # Redis
    redis_url: Optional[str] = Field(
        default="redis://localhost:6379/0", description="Redis URL"
    )

    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics")
    metrics_port: int = Field(default=9090, description="Metrics port")

    @validator("chroma_persist_directory", pre=True)
    def ensure_path(cls, v):
        if isinstance(v, str):
            return Path(v)
        return v

    @validator("jwt_secret_key")
    def validate_jwt_secret(cls, v):
        if v == "change-this-in-production":
            import warnings

            warnings.warn(
                "Using default JWT secret key. Please change this in production!",
                UserWarning,
            )
        return v

    def create_directories(self):
        """Create necessary directories if they don't exist"""
        self.chroma_persist_directory.mkdir(parents=True, exist_ok=True)
        Path("./data").mkdir(exist_ok=True)
        Path("./logs").mkdir(exist_ok=True)


settings = Settings()