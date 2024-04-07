import psycopg2
from typing import List, Dict


class PostgreSqlMetaDataLoader:
    def __init__(self, host: str, port: int, username: str, password: str, database_schema: str) -> None:
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database_schema = database_schema

    def _get_connection(self):
        return psycopg2.connect(host=self.host,
                                port=self.port,
                                user=self.username,
                                password=self.password,
                                database=self.database_schema)

    def get_table_names(self) -> List[str]:

        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                # Fetch all table names from the specified schema
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                table_names: List[str] = [table[0] for table in tables]
                return table_names
        finally:
            connection.close()

    def get_row_count(self, table_name: str) -> int:

        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                return row_count
        finally:
            connection.close()

    def get_table_columns(self, table_name: str) -> List[str]:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
                columns = cursor.fetchall()
                column_names = [column[0] for column in columns]
                return column_names
        finally:
            connection.close()

    def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        connection = self._get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
                columns = cursor.fetchall()
                column_types = {column[0]: column[1] for column in columns}
                return column_types
        finally:
            connection.close()
