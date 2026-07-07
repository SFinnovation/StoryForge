from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "StoryForge"
    APP_ENV: str = "development"
    APP_PORT: int = 8080
    DATABASE_URL: str = "sqlite:///./storyforge.db"

    # LLM
    LLM_API_BASE: str = "https://api.deepseek.com/v1"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "deepseek-chat"
    LLM_TIMEOUT: int = 60
    LLM_MAX_TOKENS: int = 2048
    LLM_TEMPERATURE: float = 0.7

    # AI 模块
    AI_MAX_REVISIONS: int = 2
    AI_CRITIC_PASS_SCORE: int = 80
    AI_CRITIC_MODEL: str = ""
    AI_CONTEXT_MESSAGE_LIMIT: int = 20
    AI_ENABLE_CRITIC: bool = True
    AI_FALLBACK_ON_CRITIC_FAIL: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
