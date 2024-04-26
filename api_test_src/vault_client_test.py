from config.vault_client.VaultClient import VaultClient

if __name__ == '__main__':
    vault_client = VaultClient()
    print(vault_client.get_vault_secret('aws-configurations', 'aws.sso.user'))
