import os
import json
import subprocess
import logging

log = logging.getLogger(__name__)


class VaultClient:
    def __init__(self, vault_token=None, vault_addr=None):
        super().__init__()
        self.log = None
        self.vault_addr = vault_addr if vault_addr is not None else self.get_vault_addr()
        self.vault_token = vault_token if vault_token is not None else self.get_vault_token()

    def get_vault_secret(self, secret_engine, secret_name):
        curl_cmd_param = ['curl', '-H', f"X-Vault-Token: {self.vault_token}", "-X", "GET",
                          f"{self.vault_addr}/v1/{secret_engine}/data/{secret_name}"]
        try:
            result = subprocess.run(curl_cmd_param, capture_output=True, text=True)
            dictionary = json.loads(result.stdout)
            return dictionary['data']['data']
        except KeyError:
            if secret_name is None:
                raise Exception('No secret name provided')
            return None

    @staticmethod
    def get_vault_addr():
        addr = os.getenv('VAULT_ADDR')
        if addr is not None:
            return addr
        else:
            raise KeyError('VAULT_ADDR environment variable is not set')

    @staticmethod
    def get_vault_token():
        token = os.getenv('VAULT_TOKEN')
        if token is not None:
            return token
        else:
            raise KeyError('VAULT_TOKEN environment variable is not set')

