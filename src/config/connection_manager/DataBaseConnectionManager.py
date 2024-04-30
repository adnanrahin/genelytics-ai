from config.mysql.MySqlMetaDataLoader import MySqlMetaDataLoader
from config.postgres.PostgreSqlMetaDataLoader import PostgreSqlMetaDataLoader
from langchain_community.utilities.sql_database import SQLDatabase
from typing import List, Dict


class DataBaseConnectionManager:
    def __init__(self, db_type: str, **kwargs):
        self.db_type = db_type
        if self.db_type == 'postgresql':
            self.loader = PostgreSqlMetaDataLoader(**kwargs)
            self.data_base_type = "postgresql+psycopg2"
        elif self.db_type == 'mysql':
            self.loader = MySqlMetaDataLoader(**kwargs)
            self.data_base_type = "mysql+pymysql"
        else:
            raise ValueError("Unsupported database type")

        self.host = kwargs.get('host')
        self.port = kwargs.get('port')
        self.username = kwargs.get('username')
        self.password = kwargs.get('password')
        self.database_schema = kwargs.get('database_schema')
        self.mysql_uri = f"{self.data_base_type}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database_schema}"

    def get_mysql_url(self):
        return self.mysql_uri

    def get_table_names(self) -> List[str]:
        return self.loader.get_table_names()

    def get_row_count(self, table_name: str) -> int:
        return self.loader.get_row_count(table_name)

    def get_table_columns(self, table_name: str) -> List[str]:
        return self.loader.get_table_columns(table_name)

    def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        return self.loader.get_table_column_types(table_name)

    def get_sql_data_base(self):
        return SQLDatabase.from_uri(self.mysql_uri,
                                    include_tables=self.get_table_names(),
                                    sample_rows_in_table_info=2)
