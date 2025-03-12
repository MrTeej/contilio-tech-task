import json
from pathlib import Path


def load_config():
    config_path = Path(__file__).parent.parent / "config.json"
    try:
        with config_path.open("r") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {config_path}")
    except json.JSONDecodeError:
        raise ValueError("Configuration file contains invalid JSON")
    return config