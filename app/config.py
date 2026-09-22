from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/chatbot.db"
    llama_base_url: str = "http://127.0.0.1:8080"
    llama_model: str = "qwen2.5-1.5b-instruct-q4_k_m"
    adapter_cache_seconds: int = 60
    model_path: str = "/opt/chatbot-models/qwen2.5-1.5b-instruct-q4_k_m.gguf"
    train_lora: bool = False
    train_base_model: str = ""
    hf_token: str = ""
    cors_origins: str = "http://localhost:8000,https://thatonememeguyfromyoutube.github.io"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @property
    def cors_origin_list(self) -> list[str]:
        return [x.strip() for x in self.cors_origins.split(",") if x.strip()]

settings = Settings()
