from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    connection_str: str = "postgresql://postgres:postgres@localhost:5432/vector_db"
    index_table: str = "clinical_rag_hybrid_search"
    aact_host: str = "aact-db.ctti-clinicaltrials.org"
    aact_port: int = 5432
    aact_db: str = "aact"
    embed_dim: int = 3072


config = Settings()
