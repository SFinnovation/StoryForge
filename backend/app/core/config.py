from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "StoryForge"
    APP_ENV: str = "development"
    APP_PORT: int = 8080
    DATABASE_URL: str = "sqlite:///./storyforge.db"
    SECRET_KEY: str = "change-me-use-a-long-random-string-in-production"
    JWT_EXPIRE_MINUTES: int = 1440
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

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

    # AKP 知识引擎（Auditable Knowledge Packs）— 见 docs/akp-integration-plan.md
    AKP_ENABLED: bool = False                    # 总开关，默认关闭 → 走现有纯 LLM 路径
    AKP_ROOT: str = "third_party/akp"            # build_skill.py / templates 所在目录（相对项目根）
    AKP_PACKS_DIR: str = "data/knowledge_packs"  # 生成的 skill 包根目录（相对项目根）
    AKP_PYTHON: str = ""                         # 运行 AKP 的解释器；留空使用当前 sys.executable
    AKP_RESEARCH_TIMEOUT_MS: int = 30000         # 单次 bundle 检索超时保护
    AKP_BUILD_TIMEOUT_S: int = 600               # 建包超时
    AKP_BUNDLE_PRESET: str = "standard"          # bundle 输出预算：quick | standard

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
