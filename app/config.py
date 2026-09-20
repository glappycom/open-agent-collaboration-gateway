from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Open Agent Collaboration Gateway"
    app_version: str = "0.2.0"

    openai_api_key: str = ""
    xai_api_key: str = ""
    openai_model: str = "gpt-5.6-luna"
    xai_model: str = "grok-4.6"

    # Optional cost rates. Leave at 0 when unknown; OACG will report cost as unavailable.
    openai_input_cost_per_million: float = 0.0
    openai_output_cost_per_million: float = 0.0
    xai_input_cost_per_million: float = 0.0
    xai_output_cost_per_million: float = 0.0

    database_path: str = "./gateway.db"

    max_turns: int = 6
    max_context_chars: int = 24000
    max_prompt_chars: int = 32000
    max_provider_calls_per_request: int = 7
    max_requests_per_minute: int = 60

    approval_risk_level: str = "high"
    provider_store_responses: bool = False
    provider_timeout_seconds: float = 45.0
    max_provider_output_chars: int = 64000
    provider_max_retries: int = 2
    provider_retry_backoff_seconds: float = 0.25
    circuit_breaker_failures: int = 3
    circuit_breaker_reset_seconds: float = 30.0

    oacg_access_token: str = ""
    idempotency_ttl_seconds: int = 86400

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")


settings = Settings()
