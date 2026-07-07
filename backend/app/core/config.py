from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "StoryForge"
    APP_ENV: str = "development"
    APP_PORT: int = 8080
    DATABASE_URL: str = "sqlite:///./storyforge.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
