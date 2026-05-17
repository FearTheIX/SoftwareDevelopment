from dataclasses import dataclass
from environs import Env

@dataclass
class Config:
    app_name: str
    debug: bool

def load_config() -> Config:
    env = Env()
    env.read_env()  # читает .env из корня проекта
    return Config(
        app_name=env("APP_NAME", default="CurrencyPredictorAPI"),
        debug=env.bool("DEBUG", default=True)
    )