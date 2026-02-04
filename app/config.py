from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    SESSION_SECRET: str = "placeholder-secret"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True
    GEMINI_API_KEY: str = ""  # Gemini AI API Key

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
