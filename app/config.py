from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    connection_str: str = "postgresql://postgres:postgres@localhost:5432/vector_db"
    index_table: str = "clinical_rag_hybrid_search"
    embed_dim: int = 1536


config = Settings()
