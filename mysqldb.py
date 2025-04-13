import MySQLdb
from MySQLdb import Error


class MySQLDatabase:
    def __init__(
        self,
        host="127.0.0.1",
        database="RESUME",
        user="user",
        password="password",
        port=3307,
    ):
        """Initialize the MySQLDatabase class with the connection parameters"""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.port = port
        self.connection = None

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
            print(
                f"Successfully connected to the database {self.database} on port {self.port}"
            )
        except Error as e:
            print(f"Error: {e}")
            self.connection = None
        return self.connection

    def insert_data(self, table, columns, data):
        """Insert data into the specified table in MySQL"""
        if not self.connection:
            print("No active database connection.")
            return

        try:
            cursor = self.connection.cursor()
            placeholders = ", ".join(["%s"] * len(columns))
            insert_query = (
                f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
            )
            cursor.executemany(insert_query, data)
            self.connection.commit()
            print(f"{cursor.rowcount} rows inserted into {table}.")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def select_data(self, query):
        """Select data using a custom query and return the result"""
        if not self.connection:
            print("No active database connection.")
            return None

        try:
            cursor = self.connection.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            return result
        except Error as e:
            print(f"Error: {e}")
            return None
        finally:
            cursor.close()

    def close_connection(self):
        """Close the MySQL connection"""
        if self.connection:
            self.connection.close()
            print("MySQL connection closed.")


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

    # Insert data
    data_to_insert = [("value1", "value2"), ("value3", "value4")]
    columns = ["column1", "column2"]
    db.insert_data("test", columns, data_to_insert)

    # Select data
    query = "SELECT * FROM test"
    results = db.select_data(query)
    print(results)

    # Close connection
    db.close_connection()
