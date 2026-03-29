import os
from dataclasses import dataclass


@dataclass
class Settings:
    data_path: str = os.getenv("DATA_PATH", "data/jian.csv")


settings = Settings()