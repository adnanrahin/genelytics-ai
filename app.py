from typing import List

from config import PostgreSqlMetaDataLoader
from config.aid_lib import load_database_prompts

training_prompts = load_database_prompts('project_config/database_prompt.json')
host = '192.168.1.235'
port = '32127'  # Default PostgreSQL port
username = 'postgres'
password = 'WbrTpN3g7q'
database_schema = 'airflow_db'
pg_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_schema}"

# Create an instance of the DataBaseSchemaMetaData class
db_metadata = PostgreSqlMetaDataLoader(host, port, username, password, database_schema)

# Get table names
table_names: List[str] = db_metadata.get_table_names()
print("Table Names:", table_names)

# Get row count for a specific table
table_name = 'dag'
row_count: int = db_metadata.get_row_count(table_name)
print(f"Row count for table '{table_name}': {row_count}")

# Get column names for a specific table
table_name = 'actor'
columns: List[str] = db_metadata.get_table_columns(table_name)
print(f"Columns for table '{table_name}': {columns}")

table_name = 'actor'
column_types = db_metadata.get_table_column_types(table_name)
print(f"Column types for table '{table_name}': {column_types}")
