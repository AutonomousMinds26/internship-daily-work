import logging
import sys
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Create a root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Clean existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Stream Handler (console)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)

    # File Handler for app.log (INFO and above)
    app_log_handler = RotatingFileHandler(
        "app.log", maxBytes=10485760, backupCount=5
    )
    app_log_handler.setFormatter(formatter)
    app_log_handler.setLevel(logging.INFO)
    root_logger.addHandler(app_log_handler)

    # File Handler for error.log (WARNING/ERROR and above)
    error_log_handler = RotatingFileHandler(
        "error.log", maxBytes=10485760, backupCount=5
    )
    error_log_handler.setFormatter(formatter)
    error_log_handler.setLevel(logging.WARNING)
    root_logger.addHandler(error_log_handler)

    # Dedicated File Handler for AI Processing logs (ai_processing.log)
    ai_logger = logging.getLogger("ai_processing")
    ai_logger.setLevel(logging.INFO)
    ai_log_handler = RotatingFileHandler(
        "ai_processing.log", maxBytes=10485760, backupCount=5
    )
    ai_log_handler.setFormatter(formatter)
    ai_logger.addHandler(ai_log_handler)

    # Reduce log noise from third-party libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    logging.info("Logging successfully initialized with app.log, error.log, and ai_processing.log.")

def get_ai_logger():
    return logging.getLogger("ai_processing")

