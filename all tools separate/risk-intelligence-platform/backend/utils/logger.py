from loguru import logger
import sys

logger.remove()

logger.add(sys.stdout, level="INFO", format="{time} | {level} | {message}")

logger.add("logs/app.log", rotation="10 MB", retention="10 days")

app_logger = logger
