"""Runtime configuration for the Sensor-in-the-Loop Health Assistant skill.

Settings are resolved from environment variables so that the skill can be
deployed without modifying source code.

Environment variables:

* ``DATA_PATH`` – path to the ``jian.csv`` data file.
  Defaults to ``"data/jian.csv"`` (relative to the working directory).
"""
import os
from dataclasses import dataclass


@dataclass
class Settings:
    """Dataclass holding all runtime-configurable skill settings.

    Attributes:
        data_path: Path (absolute or relative) to the CSV health data file.
            Override via the ``DATA_PATH`` environment variable.
    """

    data_path: str = os.getenv("DATA_PATH", "data/jian.csv")


settings = Settings()