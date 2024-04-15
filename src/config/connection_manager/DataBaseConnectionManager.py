from config.mysql.MySqlMetaDataLoader import MySqlMetaDataLoader
from config.postgres.PostgreSqlMetaDataLoader import PostgreSqlMetaDataLoader

from typing import List, Dict


class DataBaseConnectionManager:
    def __init__(self, db_type: str, **kwargs):
        self.db_type = db_type
        if self.db_type == 'postgresql':
            self.loader = PostgreSqlMetaDataLoader(**kwargs)
        elif self.db_type == 'mysql':
            self.loader = MySqlMetaDataLoader(**kwargs)
        else:
            raise ValueError("Unsupported database type")

    def get_table_names(self) -> List[str]:
        return self.loader.get_table_names()

    def get_row_count(self, table_name: str) -> int:
        return self.loader.get_row_count(table_name)

    def get_table_columns(self, table_name: str) -> List[str]:
        return self.loader.get_table_columns(table_name)

    def get_table_column_types(self, table_name: str) -> Dict[str, str]:
        return self.loader.get_table_column_types(table_name)
