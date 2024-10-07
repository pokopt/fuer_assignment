
# Measurement Backend

This is a backend service for handling and processing measurements like flow, temperature, pressure, etc. The backend is built using Python and uses Docker for deployment.

## Prerequisites

- [Git](https://git-scm.com/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Python 3.10+](https://www.python.org/downloads/)

## Getting Started

### 1. Clone the Repository

To get started, clone the repository from Git:

```bash
git clone git@github.com:pokopt/fuer_assignment.git
cd fuer_assignment
```

### 2. Set Up Environment Variables

Make sure to set up the required environment variables for the app to run. You can create a `.env` file in the root of the project:

```bash
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=your_db_password
POSTGRES_HOST=db
```

### 3. Run with Docker

You can run the entire application, including the PostgreSQL database, with Docker Compose.

#### Steps:

1. Build and start the Docker containers:

    ```bash
    docker-compose --build
    ```
2. Run the container with measurements that backend should process (e.g. power and flow).
    ```bash
    docker-compose run -p 0.0.0.0:8080:8080 fuer_backend power flow
    ```

3. The backend should now be running on [http://localhost:8080](http://localhost:8080).

4. You can stop the containers with:

    ```bash
    docker-compose down
    ```

### 4. Running Locally (Without Docker)

To run the app locally without Docker:

1. Install the dependencies (preferably in a virtual environment):

    ```bash
    pip install -r requirements.txt
    ```

2. Set up environment variables (or create a `.env` file as described above).

3. Start the application (handling measurements of flow and power):

    ```bash
    PYTHONPATH=. python app/main.py power flow
    ```

4. The app will be running on [http://localhost:8080](http://localhost:8080).

### 5. Running Tests

You can run tests locally to verify that the backend is working as expected.

1. Install test dependencies (if any):

    ```bash
    pip install -r requirements_dev.txt
    ```

2. Run tests:

    ```bash
    PYTHONPATH=. pytest
    ```

---
