from aiohttp import web
from app.handlers import MeasurementRequestHandler
from log_config import setup_logging
from app.db import Database
import argparse
import asyncio
from typing import List

# Create a logger for the application
logger = setup_logging()

# Initialize the aiohttp application
database = Database()

# Function to parse command-line arguments
def parse_arguments() -> argparse.Namespace:
    """
    Create and parse command-line arguments for the application.

    :return: Parsed arguments including a list of measurement types.
    """
    logger.debug("Parsing command-line arguments.")  # Debugging argument parsing
    parser = argparse.ArgumentParser(description="Process measurement types.")
    
    # Add a positional argument to accept multiple measurement types
    # nargs='+' means it expects one or more values
    parser.add_argument('measurement_types', nargs='+', help='List of measurement types')
    
    # Parse and return the command-line arguments
    args = parser.parse_args()
    logger.info(f"Measurement types parsed: {args.measurement_types}")  # Info log for parsed arguments
    return args

# Async function to initialize the application and set up routes
async def init_app() -> web.Application:
    """
    Initialize the aiohttp application by setting up the database and routes.

    :return: An aiohttp web application.
    """
    logger.info("Initializing the application.")  # General info log for app initialization

    # Parse command-line arguments to get measurement types
    args = parse_arguments()
    
    try:
        # Initialize the database with the provided measurement types
        await database.init(args.measurement_types)
        logger.info(f"Database initialized with measurement types: {args.measurement_types}")
    except Exception as e:
        logger.error(f"Failed to initialize the database: {e}")  # Error log for DB initialization failure
        raise

    # Create the measurement request handler with the parsed arguments and database
    measurementRequestHandler = MeasurementRequestHandler(args.measurement_types, database)
    logger.debug(f"Created MeasurementRequestHandler for types: {args.measurement_types}")  # Debug log for handler creation

    # Initialize the web application
    app = web.Application()
    
    # Add routes for handling POST and GET requests
    app.router.add_post('/api/v1/measurements/{measurement_type}', measurementRequestHandler.handle_post_measurements)
    app.router.add_get('/api/v1/measurements', measurementRequestHandler.handle_get_measurements)

    logger.debug("Routes added to the application.")  # Debugging route setup

    return app

if __name__ == "__main__":
    # Log the application start
    logger.info("Application start")
    
    try:
        # Get the event loop for running async operations
        loop = asyncio.get_event_loop()

        # Initialize the app and run it using the event loop
        logger.info("Initializing the app and starting the event loop.")  # Info log for event loop starting
        app = loop.run_until_complete(init_app())

        # Start the aiohttp application on port 8080
        web.run_app(app, host="0.0.0.0", port=8080, loop=loop)
    except Exception as e:
        logger.error(f"Application encountered an error: {e}")  # Log any unhandled exception during startup
    finally:
        # Log when the application ends
        logger.info("Application end")
