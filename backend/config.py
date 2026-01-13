from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    MONGO_URI: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "api_monitor"
    
    # Security: No default value for SECRET_KEY to force it to be set in .env
    SECRET_KEY: str = Field(..., description="Secret key for JWT. Must be set in .env")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"

settings = Settings()
