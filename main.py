import os
import logging
from dotenv import load_dotenv

load_dotenv()
ENV = os.getenv("ENV", "local")

logging_handlers = [logging.StreamHandler()] + ([logging.FileHandler('app.log')] if ENV=="local" else [])

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=logging_handlers
)

logger = logging.getLogger(__name__)
logger.info("Application started")
