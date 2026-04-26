from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://smartfeed:smartfeed@localhost:5432/smartfeed"

    llm_provider: str = "ollama"
    llm_model: str = "llama3.2"
    ollama_base_url: str = "http://localhost:11434"

    anthropic_api_key: str = ""
    openai_api_key: str = ""
    openrouter_api_key: str = ""

    cors_origins: list[str] = ["http://localhost:3000"]

    topics: list[str] = [
        "Artificial Intelligence & Machine Learning",
        "Web Development & Frontend",
        "DevOps & Infrastructure",
        "Programming Languages & Tooling",
        "Cybersecurity",
        "Open Source & Linux",
        "Hardware & Electronics",
        "Science & Research",
    ]


settings = Settings()
