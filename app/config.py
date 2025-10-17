from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Configuration
    secret_key: str
    
    # GitHub Configuration
    github_token: str
    github_username: str
    
    # LLM Configuration
    llm_api_key: str
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4"
    
    # Timeout settings
    evaluation_timeout: int = 600
    github_timeout: int = 300
    
    class Config:
        env_file = ".env.local"
        case_sensitive = False


settings = Settings()