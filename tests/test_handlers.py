import pytest
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop
from unittest.mock import AsyncMock
from app.handlers import MeasurementRequestHandler
from app.db import Database
from unittest import mock
from unittest.mock import AsyncMock


class TestMeasurementHandler(AioHTTPTestCase):

    async def get_application(self):
        # Mock the database
        self.mock_db = AsyncMock(Database)

        # Set up fake data for the test
        self.mock_db.get_measurements.return_value = [
            {"flow": [{"time": 100, "value": 23.5}]},
            {"pressure": [{"time": 500, "value": 25.3}]},
        ]

        # Create an instance of the request handler with the mocked database
        self.handler = MeasurementRequestHandler(["flow", "pressure"], self.mock_db)

        # Set up the aiohttp application
        app = web.Application()
        app.router.add_get("/api/v1/measurements", self.handler.handle_get_measurements)
        app.router.add_post(
            "/api/v1/measurements/{measurement_type}",
            self.handler.handle_post_measurements,
        )
        return app

    async def test_get_measurements(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "0",
            "to_time": "1000",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 200 OK
        assert response.status == 200

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = [
            {"flow": [{"time": 100, "value": 23.5}]},
            {"pressure": [{"time": 500, "value": 25.3}]},
        ]
        assert response_json == expected_data

    async def test_get_measurements_invalid_time_range(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "1000",
            "to_time": "0",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "'from_time' has to be smaller than 'to_time'."}
        assert response_json == expected_data

    async def test_get_measurements_invalid_from_time(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "a",
            "to_time": "0",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid 'from_time' or 'to_time'."}
        assert response_json == expected_data

    async def test_get_measurements_invalid_to_time(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "0",
            "to_time": "a",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid 'from_time' or 'to_time'."}
        assert response_json == expected_data

    async def test_get_measurements_missing_time(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid 'from_time' or 'to_time'."}
        assert response_json == expected_data

    async def test_get_measurements_missing_to_time(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "0",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid 'from_time' or 'to_time'."}
        assert response_json == expected_data

    async def test_get_measurements_missing_from_time(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "to_time": "200",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid 'from_time' or 'to_time'."}
        assert response_json == expected_data

    async def test_get_empty_measurements(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "pressure",
            "from_time": "10000",
            "to_time": "50000",
        }
        self.mock_db.get_measurements.return_value = [{"flow": []}, {"temperature": []}]
        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 200 OK
        assert response.status == 200

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = [{"flow": []}, {"temperature": []}]
        assert response_json == expected_data

    async def test_get_invalid_measurements(self):
        # Define the query parameters for the request
        query_params = {
            "measurement": "flow",
            "measurement": "temperature",
            "from_time": "0",
            "to_time": "1000",
        }

        # Make the GET request to the handler
        response = await self.client.get("/api/v1/measurements", params=query_params)

        # Check if the response status is 400 OK
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": f"Unknown measurement type(s): ['temperature']"}

        assert response_json == expected_data

    async def test_post_measurements(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": 1632872334, "value": 23.5},
                {"time": 1632872340, "value": 24.2},
            ]
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post("/api/v1/measurements/flow", json=post_data)

        # Check if the response status is 204
        assert response.status == 204

        # Ensure the insert function was called with the correct data
        self.handler.db.insert_batch_measurements_name.assert_called_once_with(
            "flow", post_data["values"]
        )

    async def test_post_invalid_measurement(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": 1632872334, "value": 23.5},
                {"time": 1632872340, "value": 24.2},
            ]
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/temperature", json=post_data
        )

        # Check if the response status is 400 OK
        assert response.status == 400

        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Unknown measurement type temperature."}

        assert response_json == expected_data

    # TODO: unspecified behavior
    async def test_post_empty_values(self):
        # Define the body of the POST request
        post_data = {"values": []}

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/pressure", json=post_data
        )

        # Check if the response status is 204
        assert response.status == 204

    async def test_post_empty_body(self):
        # Define the body of the POST request
        post_data = {}

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/pressure", json=post_data
        )

        # Check if the response status is 400 OK
        assert response.status == 400
        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid JSON or missing 'values' field."}

        assert response_json == expected_data

    async def test_post_invalid_body(self):
        # Define the body of the POST request
        invalid_json = "This is not a valid JSON!"

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/pressure",
            data=invalid_json,  # Directly pass the invalid JSON as data
            headers={"Content-Type": "application/json"},  # Set appropriate header
        )

        # Check if the response status is 400 OK
        assert response.status == 400
        # Check if the response JSON matches the expected data
        response_json = await response.json()
        expected_data = {"error": "Invalid JSON or missing 'values' field."}

        assert response_json == expected_data

    async def test_post_missing_measurement(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": 1632872334, "value": 23.5},
                {"time": 1632872340, "value": 24.2},
            ]
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post("/api/v1/measurements/", json=post_data)

        # Check if the response status is 404
        assert response.status == 404

    async def test_post_invalid_value(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": 1632872334, "value": "a"},
            ]
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/pressure", json=post_data
        )

        # Check if the response status is 400
        assert response.status == 400

    async def test_post_invalid_time(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": "a", "value": 50},
            ]
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post(
            "/api/v1/measurements/pressure", json=post_data
        )

        # Check if the response status is 400
        assert response.status == 400

    async def test_post_measurements_extra_field(self):
        # Define the body of the POST request
        post_data = {
            "values": [
                {"time": 1632872334, "value": 23.5},
                {"time": 1632872340, "value": 24.2},
            ],
            "additional_field": "some value",
            "time": "1000",
            "value": 200.5
        }

        # Mock the database insert function
        self.handler.db.insert_batch_measurements_name = AsyncMock()

        # Make the POST request to the handler
        response = await self.client.post("/api/v1/measurements/flow", json=post_data)

        # Check if the response status is 204
        assert response.status == 204

        # Ensure the insert function was called with the correct data
        self.handler.db.insert_batch_measurements_name.assert_called_once_with(
            "flow", post_data["values"]
        )
 

