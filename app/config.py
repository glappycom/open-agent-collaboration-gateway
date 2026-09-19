from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Open Agent Collaboration Gateway"
    app_version: str = "0.2.0"
    openai_api_key: str = ""
    xai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    xai_model: str = "grok-4.6"
    database_path: str = "./gateway.db"
    max_turns: int = 6
    max_context_chars: int = 24000
    max_prompt_chars: int = 32000
    approval_risk_level: str = "high"
    provider_store_responses: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
