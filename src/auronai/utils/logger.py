"""
Logging configuration for AuronAI.

Provides structured logging with:
- File logging for errors (English, technical)
- Console logging for user messages (Spanish, user-friendly)
- Log rotation (daily, keep 7 days)
"""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

# Log file path
ERROR_LOG_FILE = LOGS_DIR / "auronai_errors.log"


class SpanishConsoleFormatter(logging.Formatter):
    """Formatter for user-facing console messages in Spanish."""

    # Emoji mapping for log levels
    LEVEL_EMOJI = {
        "DEBUG": "🔍",
        "INFO": "ℹ️",
        "WARNING": "⚠️",
        "ERROR": "❌",
        "CRITICAL": "🚨",
    }

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with emoji and Spanish messages."""
        emoji = self.LEVEL_EMOJI.get(record.levelname, "")
        
        # For user-facing messages, use simpler format
        if hasattr(record, "user_message"):
            return f"{emoji} {record.user_message}"
        
        # For technical messages, include more details
        return f"{emoji} [{record.levelname}] {record.getMessage()}"


class TechnicalFileFormatter(logging.Formatter):
    """Formatter for technical log files in English."""

    def __init__(self) -> None:
        super().__init__(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logger(
    name: str,
    level: int = logging.INFO,
    console_level: Optional[int] = None,
    file_level: Optional[int] = None,
) -> logging.Logger:
    """
    Set up a logger with both console and file handlers.

    Args:
        name: Logger name (usually __name__)
        level: Default logging level
        console_level: Console handler level (defaults to level)
        file_level: File handler level (defaults to WARNING)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Console handler (user-facing, Spanish)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level or level)
    console_handler.setFormatter(SpanishConsoleFormatter())
    logger.addHandler(console_handler)
    
    # File handler (technical, English)
    file_handler = TimedRotatingFileHandler(
        ERROR_LOG_FILE,
        when="midnight",
        interval=1,
        backupCount=7,  # Keep 7 days of logs
        encoding="utf-8",
    )
    file_handler.setLevel(file_level or logging.WARNING)
    file_handler.setFormatter(TechnicalFileFormatter())
    logger.addHandler(file_handler)
    
    return logger


def log_user_message(logger: logging.Logger, level: int, message: str) -> None:
    """
    Log a user-facing message in Spanish.

    Args:
        logger: Logger instance
        level: Log level (logging.INFO, logging.WARNING, etc.)
        message: User-friendly message in Spanish
    """
    # Create a log record with user_message attribute
    record = logger.makeRecord(
        logger.name,
        level,
        "(user)",
        0,
        message,
        (),
        None,
    )
    record.user_message = message
    logger.handle(record)


# Create default logger for the application
default_logger = setup_logger("auronai")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a module.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return setup_logger(name)


# Convenience functions
def info(message: str, user_facing: bool = False) -> None:
    """Log info message."""
    if user_facing:
        log_user_message(default_logger, logging.INFO, message)
    else:
        default_logger.info(message)


def warning(message: str, user_facing: bool = False) -> None:
    """Log warning message."""
    if user_facing:
        log_user_message(default_logger, logging.WARNING, message)
    else:
        default_logger.warning(message)


def error(message: str, user_facing: bool = False, exc_info: bool = False) -> None:
    """Log error message."""
    if user_facing:
        log_user_message(default_logger, logging.ERROR, message)
    else:
        default_logger.error(message, exc_info=exc_info)


def critical(message: str, user_facing: bool = False, exc_info: bool = False) -> None:
    """Log critical message."""
    if user_facing:
        log_user_message(default_logger, logging.CRITICAL, message)
    else:
        default_logger.critical(message, exc_info=exc_info)
