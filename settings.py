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

    POSTGRES_DB_TEST: str
    POSTGRES_USER_TEST: str
    POSTGRES_PASSWORD_TEST: str
    POSTGRES_HOST_TEST: str
    POSTGRES_PORT_TEST: int

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

    @property
    def TEST_DATABASE_URL(self) -> str:
        return (f"postgresql+asyncpg://{self.POSTGRES_USER_TEST}:{self.POSTGRES_PASSWORD_TEST}@"
                f"{self.POSTGRES_HOST_TEST}:{self.POSTGRES_PORT_TEST}/{self.POSTGRES_DB_TEST}")

    @property
    def TEST_SYNC_DATABASE_URL(self) -> str:
        return (f"postgresql://{self.POSTGRES_USER_TEST}:{self.POSTGRES_PASSWORD_TEST}@"
                f"{self.POSTGRES_HOST_TEST}:{self.POSTGRES_PORT_TEST}/{self.POSTGRES_DB_TEST}")

    model_config = ConfigDict(from_attributes=True)


settings = Settings()