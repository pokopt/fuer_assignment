import logging
import os
import sys

# Function to set up logging
def setup_logging():
    # Get log level from the environment, default to INFO if not set
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()

    # Create the root logger
    logger = logging.getLogger('fuer_logger')
    logger.setLevel(getattr(logging, log_level, logging.INFO))

    # Set up the logging handler (logging to stdout)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    # Clear any existing handlers (in case this function is called multiple times)
    if logger.hasHandlers():
        logger.handlers.clear()

    # Add the handler to the logger
    logger.addHandler(handler)
    return logger