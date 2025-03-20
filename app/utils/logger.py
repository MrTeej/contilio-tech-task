import logging

from app.utils.config_loader import load_config

config = load_config()
logging_config = config.get("logging", {})

logger = logging.getLogger("Contilio_Train_API")
logger.setLevel(getattr(logging, logging_config.get("log_level", "DEBUG").upper()))

console_handler = logging.StreamHandler()

formatter = logging.Formatter(
    logging_config.get(
        "log_format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
