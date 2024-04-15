from config.connection_manager.DataBaseConnectionManager import DataBaseConnectionManager

host = 'localhost'
port = '3305'
username = 'root'
password = 'root'
database_schema = 'nasa_space_exploration_database'
data_base_type = "mysql+pymysql"
mysql_uri = f"{data_base_type}://{username}:{password}@{host}:{port}/{database_schema}"
db_metadata = DataBaseConnectionManager(db_type='mysql', host='localhost', port='3305', username='root',
                                        password='root', database_schema='nasa_space_exploration_database')

print(db)

print(db_metadata.get_table_names())
