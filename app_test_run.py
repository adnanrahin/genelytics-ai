from typing import List, Dict, Any

from meta_data_loader.mysql_meta_loader.mysql_meta_data_loader import MySqlMetaDataLoader

host = 'localhost'
port = 3305
username = 'root'
password = 'root'
database_schema = 'sakila'

# Create an instance of the DataBaseSchemaMetaData class
db_metadata = MySqlMetaDataLoader(host, port, username, password, database_schema)

# Get table names
table_names: List[str] = db_metadata.get_table_names()
print("Table Names:", table_names)

# Get row count for a specific table
table_name = 'actor'
row_count: int = db_metadata.get_row_count(table_name)
print(f"Row count for table '{table_name}': {row_count}")

# Get column names for a specific table
table_name = 'actor'
columns: List[str] = db_metadata.get_table_columns(table_name)
print(f"Columns for table '{table_name}': {columns}")

table_name = 'actor'
column_types = db_metadata.get_table_column_types(table_name)
print(f"Column types for table '{table_name}': {column_types}")
