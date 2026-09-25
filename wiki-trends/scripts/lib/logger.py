import logging
from logging.handlers import RotatingFileHandler
import os
import sys
from typing import Optional

DEFAULT_LOG_FILE = "wiki_trends.log"
DEFAULT_MAX_BYTES = 5 * 1024 * 1024  # 5 MB per file
DEFAULT_BACKUP_COUNT = 3  # Keep at most 3 backup files (total ~20 MB max)
_current_log_file: Optional[str] = None

class ComponentFormatter(logging.Formatter):
    """Formatter that injects a default component name if none is provided."""
    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "component"):
            record.component = record.levelname
        return super().format(record)

def setup_logger(
    verbose: bool = False,
    quiet: bool = False,
    log_file: Optional[str] = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
    backup_count: int = DEFAULT_BACKUP_COUNT
) -> logging.Logger:
    """
    Configure the wiki_trends logger that writes to a rotated .log file.
    
    Levels:
    - quiet: WARNING only
    - default: INFO
    - verbose: DEBUG
    
    Format: [%(asctime)s] [%(component)s] %(message)s
    """
    global _current_log_file
    logger = logging.getLogger("wiki_trends")
    
    # Avoid duplicate handlers if setup_logger is called multiple times
    if logger.handlers:
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
        
    if quiet:
        level = logging.WARNING
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
        
    logger.setLevel(level)
    
    target_log_file = log_file or os.environ.get("WIKI_TRENDS_LOG_FILE", DEFAULT_LOG_FILE)
    try:
        target_max_bytes = int(os.environ.get("WIKI_TRENDS_LOG_MAX_BYTES", max_bytes))
    except (ValueError, TypeError):
        target_max_bytes = max_bytes
    try:
        target_backup_count = int(os.environ.get("WIKI_TRENDS_LOG_BACKUP_COUNT", backup_count))
    except (ValueError, TypeError):
        target_backup_count = backup_count
    
    # Ensure directory exists if path contains a directory component
    log_dir = os.path.dirname(os.path.abspath(target_log_file))
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        
    handler = RotatingFileHandler(
        target_log_file,
        maxBytes=target_max_bytes,
        backupCount=target_backup_count,
        encoding="utf-8"
    )
    handler.setLevel(level)
    
    formatter = ComponentFormatter("[%(asctime)s] [%(component)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    
    logger.addHandler(handler)
    logger.propagate = False
    _current_log_file = target_log_file
    return logger

def get_log_file() -> Optional[str]:
    """Get the path to the current log file."""
    return _current_log_file

def get_logger() -> logging.Logger:
    """Get the wiki_trends logger, initializing it if not already configured."""
    logger = logging.getLogger("wiki_trends")
    if not logger.handlers:
        return setup_logger()
    return logger

def log(component: str, message: str, level: int = logging.INFO) -> None:
    """Convenience function to log a message with a specific component tag."""
    logger = get_logger()
    logger.log(level, message, extra={"component": component})

