import asyncpg
import os
import logging
import functools
from typing import List, Dict

# Use the existing logger 'fuer_logger'
logger = logging.getLogger("fuer_logger")

class Database:
    def __init__(self):
        """
        Initialize the database class with a connection pool and a dictionary
        for storing measurement types.
        """
        self.pool = None
        self.measurement_types: Dict[str, int] = dict()
        logger.info("Database class initialized.")

    async def init(self, measurement_names: List[str]) -> None:
        """
        Initialize the database connection pool and create/drop tables.

        :param measurement_names: List of measurement types (e.g., ['temperature', 'pressure']).
        """
        logger.info(f"Initializing database with measurement types: {measurement_names}")
        logger.debug(f'Connecting to DB with user: {os.getenv("POSTGRES_USER")}, host: {os.getenv("POSTGRES_HOST")}')

        self.pool = await asyncpg.create_pool(
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            database=os.getenv("POSTGRES_DB"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            min_size=len(measurement_names),  # Minimum connections in the pool
            max_size=len(measurement_names) + 2,  # Maximum connections in the pool
        )
        logger.info("Connection pool created.")
        
        await self.drop_tables()
        await self.init_tables(measurement_names)

    # Decorator for managing connection acquisition and release
    def with_connection(func):
        @functools.wraps(func)
        async def wrapper(self, *args, **kwargs):
            conn = None
            try:
                # Acquire a connection from the pool
                conn = await self.pool.acquire()
                logger.debug("Connection acquired from pool.")
                # Pass the connection to the decorated function
                return await func(self, conn, *args, **kwargs)
            except Exception as e:
                logger.error(f"Database operation failed: {e}")
                raise
            finally:
                if conn is not None:
                    await self.pool.release(conn)
                    logger.debug("Connection released back to pool.")
        return wrapper

    async def close(self) -> None:
        """
        Close the connection pool.
        """
        if self.pool is not None:
            await self.pool.close()
            logger.info("Connection pool closed.")

    @with_connection
    async def init_tables(self, conn, measurement_names: List[str]) -> None:
        """
        Create the necessary tables and partitions for measurements.

        :param measurement_names: List of measurement types.
        """
        logger.info("Creating tables and partitions.")
        
        # Create measurement_type table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement_type (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL UNIQUE
            );
            """
        )
        logger.debug("Table 'measurement_type' created or already exists.")

        # Create partitions for each measurement type
        self.measurement_types = {name: idx for idx, name in enumerate(measurement_names, start=1)}

        for name, id in self.measurement_types.items():
            # Insert measurement type into the table
            await conn.execute(
                """
                INSERT INTO measurement_type (id, name)
                VALUES ($1, $2)
                ON CONFLICT (name) DO NOTHING;
                """,
                id,
                name,
            )
            logger.debug(f"Measurement type '{name}' inserted with ID {id}.")

        # Create partitioned measurement table
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS measurement (
                measurement_type_id INT NOT NULL,   
                time INT NOT NULL,                  
                value FLOAT NOT NULL                
            ) PARTITION BY LIST (measurement_type_id);
            """
        )
        logger.debug("Table 'measurement' created or already exists.")

        # Create partitions for each measurement type
        for name, id in self.measurement_types.items():
            partition_name = f"measurement_{name}_partition"
            await conn.execute(
                f"""
                CREATE TABLE {partition_name} PARTITION OF measurement
                FOR VALUES IN ({id});
                """
            )
            logger.debug(f"Partition '{partition_name}' created for measurement type '{name}'.")

    @with_connection
    async def drop_tables(self, conn) -> None:
        """
        Drop the measurement and measurement_type tables.

        :param conn: The active database connection.
        """
        logger.info("Dropping tables 'measurement' and 'measurement_type'.")
        await conn.execute(
            """
            DROP TABLE IF EXISTS measurement CASCADE;
            DROP TABLE IF EXISTS measurement_type CASCADE;
            """
        )
        logger.info("Tables 'measurement' and 'measurement_type' dropped successfully.")

    @with_connection
    async def insert_batch_measurements_id(
        self, conn, measurement_type_id: int, measurement_values: List[Dict[str, float]]
    ) -> None:
        """
        Insert a batch of measurements into the measurement table.

        :param measurement_type_id: ID of the measurement type (e.g., 1 for temperature).
        :param measurement_values: List of dictionaries, each containing 'time' and 'value'.
        """
        logger.info(f"Inserting batch of measurements for measurement_type_id: {measurement_type_id}.")
        await conn.executemany(
            """
            INSERT INTO measurement (measurement_type_id, time, value)
            VALUES ($1, $2, $3)
            """,
            [(measurement_type_id, m["time"], m["value"]) for m in measurement_values],
        )
        logger.info(f"Inserted {len(measurement_values)} measurements for measurement_type_id {measurement_type_id}.")

    async def insert_batch_measurements_name(
        self, measurement_name: str, measurement_values: List[Dict[str, float]]
    ) -> None:
        """
        Insert a batch of measurements based on the measurement type name.

        :param measurement_name: The name of the measurement type (e.g., 'temperature').
        :param measurement_values: List of dictionaries, each containing 'time' and 'value'.
        """
        logger.info(f"Inserting measurements for '{measurement_name}'.")
        await self.insert_batch_measurements_id(
            self.measurement_types[measurement_name], measurement_values
        )

    @with_connection
    async def get_measurements(
        self, conn, measurement_names: List[str], time_from: int, time_to: int
    ) -> List[Dict[str, List[Dict[str, float]]]]:
        """
        Get measurements for the given types and time range.

        :param measurement_names: List of measurement type names.
        :param time_from: Start time (timestamp).
        :param time_to: End time (timestamp).
        :return: List of dictionaries with measurement data for each type.
        """
        logger.info(f"Fetching measurements for: {measurement_names} from {time_from} to {time_to}.")
        results = []

        for measurement_name in measurement_names:
            partition_name = f"measurement_{measurement_name}_partition"
            query = f'''
                SELECT time, value
                FROM {partition_name}
                WHERE time >= $1 AND time <= $2;
            '''
            rows = await conn.fetch(query, time_from, time_to)
            measurement_data = {
                measurement_name: [{"time": row["time"], "value": row["value"]} for row in rows]
            }
            logger.debug(f"Fetched {len(rows)} rows for '{measurement_name}'.")
            results.append(measurement_data)

        logger.info(f"Finished fetching measurements.")
        return results
