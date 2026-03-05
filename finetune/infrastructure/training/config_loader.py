import os

import yaml


class ConfigLoader:
    """Load YAML config files from configs/training/."""

    def __init__(self, config_dir: str = "configs/training"):
        self.config_dir = config_dir

    def load(self, config_name: str) -> dict:
        path = os.path.join(self.config_dir, f"{config_name}.yml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config not found: {path}")
        with open(path) as f:
            config = yaml.safe_load(f)
        config["_source"] = path
        return config
