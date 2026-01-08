from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # --- Project Metadata ---
    PROJECT_NAME: str
    VERSION: str

    # --- Model Paths ---
    HELMET_MODEL_PATH: str
    PLATE_MODEL_PATH: str
    HSRP_MODEL_PATH: str

    # --- Business Rules ---
    HELMET_CONF_THRESHOLD: float
    HSRP_CONF_THRESHOLD: float = 0.5
    OCR_CONF_THRESHOLD: float 

    # --- Database & Storage ---
    DATABASE_URL: str
    STORAGE_DIR: str

    # --- API ---
    HOST: str
    PORT: int
    DEBUG: bool

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
