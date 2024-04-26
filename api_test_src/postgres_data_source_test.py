from typing import List, Dict, Any
from config.vault_client.VaultClient import VaultClient
from config.postgres.PostgreSqlMetaDataLoader import PostgreSqlMetaDataLoader

data_base_config = VaultClient().get_vault_secret('application-key-vault', 'psotgres_db_secrets')
host = data_base_config['postgres_host']
port = data_base_config['postgres_port']
username = data_base_config['db_user']
password = data_base_config['db_password']
database_schema = data_base_config['database_schema']
pg_uri = f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database_schema}"

# Create an instance of the DataBaseSchemaMetaData class
db_metadata = PostgreSqlMetaDataLoader(host=host, port=port, username=username, password=password,
                                       database_schema=database_schema)

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
