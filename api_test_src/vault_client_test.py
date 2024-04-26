from config.vault_client.VaultClient import VaultClient

if __name__ == '__main__':
    data_base_config = VaultClient().get_vault_secret('application-key-vault', 'dev_mysql_docker_db')
    host = data_base_config['host']
    port = data_base_config['port']
    username = data_base_config['db_user']
    password = data_base_config['db_password']
    database_schema = data_base_config['database_schema']
    print(data_base_config)
