from dotenv import load_dotenv
from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent

class Settings(BaseSettings):
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: int

    LOG_LEVEL: str = "INFO"

    JWT_PRIVATE_KEY: Path = PROJECT_ROOT / "certs" / "private.pem"
    JWT_PUBLIC_KEY: Path = PROJECT_ROOT / "certs" / "public.pem"
    ALGORITHM: str = "RS256"

    @property
    def DATABASE_URL(self) -> str:
        return (f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return (f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}")


    model_config = ConfigDict(from_attributes=True)


settings = Settings()