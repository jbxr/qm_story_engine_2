"""Configuration management using Pydantic Settings"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database Configuration
    supabase_url: str = Field(..., description="Supabase project URL")
    supabase_key: str = Field(..., description="Supabase anon key")
    supabase_service_key: str = Field(..., description="Supabase service role key")
    
    # OpenAI Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_model: str = Field(default="gpt-4o-mini", description="Default OpenAI model")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", 
        description="OpenAI embedding model"
    )
    
    # Alternative LLM Configuration
    groq_api_key: str = Field(default="", description="Groq API key")
    groq_model: str = Field(default="llama-3.1-70b-versatile", description="Groq model")
    
    # Application Configuration
    app_env: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=True, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_prefix: str = Field(default="/api/v1", description="API prefix")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="CORS allow credentials")
    
    # Security Configuration
    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for session management"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, 
        description="Access token expiration time"
    )
    
    # Performance Configuration
    max_embedding_batch_size: int = Field(
        default=100, 
        description="Maximum batch size for embeddings"
    )
    default_page_size: int = Field(default=50, description="Default pagination size")
    max_page_size: int = Field(default=1000, description="Maximum pagination size")
    
    # Feature Flags
    enable_llm_features: bool = Field(default=True, description="Enable LLM features")
    enable_semantic_search: bool = Field(default=True, description="Enable semantic search")
    enable_knowledge_snapshots: bool = Field(
        default=True, 
        description="Enable knowledge snapshots"
    )
    
    @property
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.app_env.lower() == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.app_env.lower() == "production"


# Global settings instance - lazy loaded
_settings: Settings = None


def get_settings() -> Settings:
    """Get application settings (for dependency injection)"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings