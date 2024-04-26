from typing import List, Dict, Any
from config.vault_client.VaultClient import VaultClient
from config.mysql.MySqlMetaDataLoader import MySqlMetaDataLoader

data_base_config = VaultClient().get_vault_secret('application-key-vault', 'dev_mysql_docker_db')
host = data_base_config['host']
port = data_base_config['port']
username = data_base_config['db_user']
password = data_base_config['db_password']
database_schema = data_base_config['database_schema']
mysql_uri = f"mysql+pymysql://{username}:{password}@{host}:{port}/{database_schema}"

# Create an instance of the DataBaseSchemaMetaData class
db_metadata = MySqlMetaDataLoader(host=host, port=port, username=username, password=password,
                                  database_schema=database_schema)
# db_metadata = MySqlMetaDataLoader(host, port, username, password, database_schema)

# Get table names
table_names: List[str] = db_metadata.get_table_names()
print("Table Names:", table_names)

# Get row count for a specific table
table_name = 'astronaut_info'
row_count: int = db_metadata.get_row_count(table_name)
print(f"Row count for table '{table_name}': {row_count}")

# Get column names for a specific table
table_name = 'astronaut_info'
columns: List[str] = db_metadata.get_table_columns(table_name)
print(f"Columns for table '{table_name}': {columns}")

table_name = 'astronaut_info'
column_types = db_metadata.get_table_column_types(table_name)
print(f"Column types for table '{table_name}': {column_types}")
