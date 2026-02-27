import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    OPENROUTER_API_KEY: str
    LLM_MODEL: str = "mistralai/mistral-7b-instruct:free"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
