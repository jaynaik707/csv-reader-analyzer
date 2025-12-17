"""
Logging configuration for Order Pipeline
Provides consistent logging across all modules
"""
import logging
import sys
from pathlib import Path


def setup_logging(
    level: int = logging.INFO,
    log_file: str = 'pipeline.log',
    log_to_console: bool = True,
    log_to_file: bool = True
) -> None:
    """
    Configure application-wide logging
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        log_to_console: Whether to log to console
        log_to_file: Whether to log to file
    """
    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)-25s - %(levelname)-8s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create handlers
    handlers = []
    
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        handlers.append(console_handler)
    
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True  # Override any existing configuration
    )
    
    # Reduce noise from kafka library (optional)
    logging.getLogger('kafka').setLevel(logging.WARNING)
    
    # Log that logging is configured
    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")
    logger.debug(f"Log level: {logging.getLevelName(level)}")
    logger.debug(f"Console logging: {log_to_console}")
    logger.debug(f"File logging: {log_to_file} (file: {log_file})")


