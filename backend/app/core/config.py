from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Ecowise AI Platform API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"

    # Can toggle LLM integration flags or embedder models here
    EMBEDDER_MODEL: str = "all-MiniLM-L6-v2"

    ECOWISE_DATABASE_URL: str = "postgresql+psycopg://ecowise:ecowise@localhost:5432/ecowise"
    ML_WORKER_ENABLED: bool = True
    ML_WORKER_POLL_INTERVAL_SECONDS: int = 5
    ML_WORKER_BATCH_SIZE: int = 5
    ML_MAX_MATCH_RESULTS: int = 10

    class Config:
        case_sensitive = True

settings = Settings()
