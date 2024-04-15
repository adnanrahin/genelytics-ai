import pymysql
from typing import List, Dict

from pymysql.cursors import DictCursor


class MySqlMetaDataLoader:
    def __init__(self, **kwargs):
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.database_schema = kwargs.get('database_schema')

    def get_connection(self):
        # Establish connection to the MySQL database
        return pymysql.connect(host=self.host,
                               port=int(self.port),
                               user=self.username,
                               password=self.password,
                               db=self.database_schema,
                               cursorclass=DictCursor)  # Use DictCursor here

    def get_table_names(self) -> List[str]:
        # Establish connection to the MySQL database
        connection = self.get_connection()

        try:
            # Create a cursor object to execute SQL queries
            with connection.cursor() as cursor:
                # Fetch all table names from the specified schema
                cursor.execute("SHOW TABLES")
                tables = cursor.fetchall()
                table_names: List[str] = [table['Tables_in_' + self.database_schema] for table in tables]
                return table_names
        finally:
            # Close the database connection
            connection.close()

    def get_row_count(self, table_name: str) -> int:
        # Establish connection to the MySQL database
        connection = self.get_connection()

        try:
            # Create a cursor object to execute SQL queries
            with connection.cursor() as cursor:
                # Execute SQL query to get row count for the table
                cursor.execute(f"SELECT COUNT(*) AS row_count FROM {table_name}")
                row_count = cursor.fetchone()['row_count']
                return row_count
        finally:
            # Close the database connection
            connection.close()

    def get_table_columns(self, table_name: str) -> List[str]:
        # Establish connection to the MySQL database
        connection = self.get_connection()
        try:
            # Create a cursor object to execute SQL queries
            with connection.cursor() as cursor:
                # Execute SQL query to get column names for the table
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = cursor.fetchall()
                column_names = [column['Field'] for column in columns]
                return column_names
        finally:
            # Close the database connection
            connection.close()

    def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        # Establish connection to the MySQL database
        connection = self.get_connection()

        try:
            # Create a cursor object to execute SQL queries
            with connection.cursor() as cursor:
                # Execute SQL query to get column types for the table
                cursor.execute(f"SHOW COLUMNS FROM {table_name}")
                columns = cursor.fetchall()
                column_types = {column['Field']: column['Type'] for column in columns}
                return column_types
        finally:
            # Close the database connection
            connection.close()
