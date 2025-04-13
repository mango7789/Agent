import os, logging
import MySQLdb
from MySQLdb import Error
from datetime import datetime


class MySQLDatabase:
    def __init__(
        self,
        host: str = "127.0.0.1",
        database: str = "RESUME",
        user: str = "testuser",
        password: str = "123456",
        port: int = 3307,
        debug: bool = False,
    ):
        """Initialize the MySQLDatabase class with the connection parameters"""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.debug = debug
        self.connection = None

        # Get the current user's home directory and generate a timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_directory = f"/home/resume/log/{user}"

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_file = os.path.join(log_directory, f"{timestamp}.log")

        # Set up logging to file and stream
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
        )
        self.logger = logging.getLogger()

    def create_connection(self):
        """Create and return a MySQL database connection"""
        try:
            self.connection = MySQLdb.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port,
            )
            self.logger.info(
                f"Successfully connected to the database {self.database} on port {self.port}"
            )
        except Error as e:
            self.logger.error(e)
            self.connection = None
        return self.connection

    def insert_data(self, table: str, columns: list, data: list[tuple]):
        """Insert data into the specified table in MySQL"""
        if not self.connection:
            self.logger.error("No active database connection.")
            return

        try:
            cursor = self.connection.cursor()
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = (
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            )
            cursor.executemany(insert_query, data)
            self.connection.commit()
            self.logger.info(f"{cursor.rowcount} rows inserted into {table}.")
        except Error as e:
            self.logger.error(e)
        finally:
            cursor.close()

    def select_data(self, query: str):
        """Select data using a custom query and return the result"""
        if not self.connection:
            self.logger.error("No active database connection.")
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            self.logger.info(f"Query executed successfully: {query}")
            if self.debug:
                self.logger.debug(f"Query result: {result}")
            return result
        except Error as e:
            self.logger.error(f"Failed to execute query: {query}")
            self.logger.error(e)
            return None
        finally:
            cursor.close()

    def close_connection(self):
        """Close the MySQL connection"""
        if self.connection:
            self.connection.close()
            self.logger.info("MySQL connection closed.")


if __name__ == "__main__":
    # Initialize the database connection
    db = MySQLDatabase(
        user="testuser",
        password="123456",
        database="RESUME",
        host="127.0.0.1",
        port=3307,
    )

    # Create connection
    connection = db.create_connection()

    if connection:
        # Insert data
        data_to_insert = [("value1", "value2"), ("value3", "value4")]
        columns = ["column1", "column2"]
        db.insert_data("test", columns, data_to_insert)

        # Select data
        query = "SELECT * FROM test"
        db.select_data(query)

        # Close connection
        db.close_connection()
