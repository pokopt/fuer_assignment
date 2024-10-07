from aiohttp import web
import json
import logging
from .db import Database

# Get a logger specific to this module
logger = logging.getLogger('fuer_logger')

def validate_measurement_data(data: list[dict]) -> None:
    """
    Validate a list of measurement data dictionaries.

    :param data: List of dictionaries, each containing 'time' and 'value'.
    :raises ValidationError: If any entry in the list contains invalid data.
    """
    for idx, entry in enumerate(data):
        if not isinstance(entry, dict):
            raise ValidationError(f"Entry {idx} is not a dictionary: {entry}")
        
        if 'time' not in entry or 'value' not in entry:
            raise ValidationError(f"Entry {idx} is missing 'time' or 'value': {entry}")
        
        if not isinstance(entry['time'], int):
            raise ValidationError(f"Entry {idx} has invalid 'time': {entry['time']} (should be int)")
        
        if not isinstance(entry['value'], (int, float)):
            raise ValidationError(f"Entry {idx} has invalid 'value': {entry['value']} (should be int or float)")

    # If all entries are valid, return None
    return


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

class MeasurementRequestHandler:
    def __init__(self, measurements: list[str], db: Database):
        """
        Initialize the request handler.

        :param measurements: List of supported measurement types.
        :param db: Instance of the Database class to perform database operations.
        """
        self.db = db  # Store the database connection or pool
        self.measurements = measurements  # List of valid measurement types
        logger.info(f"MeasurementRequestHandler initialized with supported measurements: {measurements}")

    async def handle_post_measurements(self, request: web.Request) -> web.Response:
        """
        Handle POST requests for adding measurements.

        Expects a JSON body with a 'values' field containing a list of timestamped measurements.

        :param request: The aiohttp request object.
        :return: A JSON response with success or error message.
        """
        # Extract measurement_type from the URL path
        measurement_type = request.match_info['measurement_type']
        logger.debug(f"Handling POST request for measurement_type: {measurement_type}")
        
        # Check if the measurement_type is valid
        if measurement_type not in self.measurements:
            logger.warning(f"Invalid measurement type received: {measurement_type}")
            return web.json_response({"error": f"Unknown measurement type {measurement_type}."}, status=400)
         
        # Parse the request body (JSON data)
        try:
            data = await request.json()
            values = data['values']  # List of {"time": <timestamp>, "value": <float>}
            logger.error(values)
            validate_measurement_data(values)
        except (json.JSONDecodeError, KeyError, ValidationError) as e:
            logger.error(f"Error parsing JSON request body: {e}")
            return web.json_response({"error": "Invalid JSON or missing 'values' field."}, status=400)

        # Log the measurement_type and values for debugging
        logger.info(f"Received measurements for {measurement_type}: {values}")
        
        # Insert the data into the database
        try:
            await self.db.insert_batch_measurements_name(measurement_type, values)
            logger.info(f"Successfully inserted measurements for {measurement_type}.")
        except Exception as e:
            logger.error(f"Error inserting measurements: {e}")
            return web.json_response({"error": str(e)}, status=500)
        
        # Respond with a success message
        return web.json_response(status=204)

    async def handle_get_measurements(self, request: web.Request) -> web.Response:
        """
        Handle GET requests to retrieve measurements.

        Query parameters:
        - 'measurement': string (can be specified multiple times)
        - 'from_time': timestamp (start time)
        - 'to_time': timestamp (end time)

        :param request: The aiohttp request object.
        :return: A JSON response containing measurement data or error message.
        """
        # Get 'measurement' query parameters (can be multiple)
        measurements = request.query.getall('measurement')
        logger.debug(f"GET request received for measurements: {measurements}")
        
        # Get 'from_time' and 'to_time' query parameters
        from_time = request.query.get('from_time')
        to_time = request.query.get('to_time')

        # Convert 'from_time' and 'to_time' to integers (timestamps)
        try:
            from_time = int(from_time)
            to_time = int(to_time)
            logger.debug(f"Fetching measurements from {from_time} to {to_time}")
        except (TypeError, ValueError):
            logger.error(f"Invalid 'from_time' or 'to_time' received: {from_time}, {to_time}")
            return web.json_response({"error": "Invalid 'from_time' or 'to_time'."}, status=400)
        
        if (from_time >= to_time):
            logger.error(f"'from_time' has to be smaller than 'to_time'.")
            return web.json_response({"error": "'from_time' has to be smaller than 'to_time'."}, status=400) 
        
        unknown_measurements = [meas for meas in measurements if meas not in self.measurements]
        if unknown_measurements:
            logger.warning(f"Unknown measurement types requested: {unknown_measurements}")
            return web.json_response({"error": f'Unknown measurement type(s): {unknown_measurements}'}, status=400)


        if not measurements:
            logger.warning("No measurements provided in GET request.")
            return web.json_response({"error": "At least one 'measurement' must be provided."}, status=400)

        try:
            # Call the database method to get measurements
            result = await self.db.get_measurements(measurements, from_time, to_time)
            logger.info(f"Successfully fetched measurements for {measurements}.")
            
            # Return the result as a JSON response
            return web.json_response(result, status=200)

        except Exception as e:
            logger.error(f"Error fetching measurements: {e}")
            return web.json_response({"error": str(e)}, status=500)
