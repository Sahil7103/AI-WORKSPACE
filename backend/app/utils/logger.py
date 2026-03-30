"""
Logging configuration.
"""

import logging
import sys
from pathlib import Path

from app.core.config import settings

# Create logs directory
logs_dir = Path("logs")
logs_dir.mkdir(exist_ok=True)

# Create logger
logger = logging.getLogger("ai_copilot")

# Set level
level = logging.DEBUG if settings.debug else logging.INFO
logger.setLevel(level)

# Create formatters
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(level)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler
file_handler = logging.FileHandler(logs_dir / "app.log")
file_handler.setLevel(level)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
