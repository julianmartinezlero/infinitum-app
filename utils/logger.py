import sys
import os
from loguru import logger



def get_resource_path(log_path):

    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    log_file = os.path.join(base_path, log_path)
    return log_file


def setup_logger(log_file: str = "app.log"):
    """
    Configures the global loguru logger with a file sink and console sink.
    Returns the configured logger.
    """

    log_file = get_resource_path(log_file)
    print(log_file)

    logger.remove()
    
    # Console output - only if stdout is available (not None in windowed PyInstaller)
    if sys.stdout is not None:
        logger.add(sys.stdout, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    
    # File output
    logger.add(log_file, rotation="10 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}", level="DEBUG")
    
    return logger

log = setup_logger()
