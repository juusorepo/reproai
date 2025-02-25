import logging
import sys

def get_logger(name: str, log_file: str = "app.log") -> logging.Logger:
    """
    Creates and configures a logger with both console and file handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # or INFO, etc.

    # Avoid adding multiple handlers if logger is already configured
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(logging.DEBUG)
        console_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_format)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_format = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_format)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger