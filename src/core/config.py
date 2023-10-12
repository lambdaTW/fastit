import pathlib
import typing

import pydantic_settings

PROJECT_PATH = pathlib.Path(__file__).parent.parent
print(PROJECT_PATH)


class Settings(pydantic_settings.BaseSettings):
    authjwt_secret_key: str = "secret"
    DATABASE_URL: str
    MODE: typing.Literal["test", "development", "production"] = "development"
    model_config = pydantic_settings.SettingsConfigDict(
        env_file=PROJECT_PATH / ".env",
        extra="ignore",
    )
    INIT_SUPERUSER_USERNAME: typing.Optional[str] = None
    INIT_SUPERUSER_PASSWORD: typing.Optional[str] = None
