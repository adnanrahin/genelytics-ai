import psycopg2
from typing import List, Dict


class PostgreSqlMetaDataLoader:
    def __init__(self, **kwargs) -> None:
        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.database_schema = kwargs.get('database_schema')

    def get_connection(self):
        return psycopg2.connect(host=self.host,
                                port=self.port,
                                user=self.username,
                                password=self.password,
                                database=self.database_schema)

    def get_table_names(self) -> List[str]:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
                tables = cursor.fetchall()
                table_names: List[str] = [table[0] for table in tables]
                return table_names
        finally:
            connection.close()

    def get_row_count(self, table_name: str) -> int:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                return row_count
        finally:
            connection.close()

    def get_table_columns(self, table_name: str) -> List[str]:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table_name}'")
                columns = cursor.fetchall()
                column_names = [column[0] for column in columns]
                return column_names
        finally:
            connection.close()

    def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}'")
                columns = cursor.fetchall()
                column_types = {column[0]: column[1] for column in columns}
                return column_types
        finally:
            connection.close()
