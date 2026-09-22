from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/chatbot.db"
    llama_base_url: str = "http://127.0.0.1:8080"
    llama_model: str = "prism-ml/Ternary-Bonsai-2-27B-gguf"
    adapter_cache_seconds: int = 60
    model_path: str = "/opt/chatbot-models/Ternary-Bonsai-2-27B-PQ2_0.gguf"
    train_lora: bool = False
    train_base_model: str = ""
    hf_token: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

settings = Settings()
