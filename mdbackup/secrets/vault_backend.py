from typing import Dict

import requests

from mdbackup.secrets.secrets import AbstractSecretsBackend


class VaultSecretsBackend(AbstractSecretsBackend):
    def __init__(self, config: Dict[str, any]):
        super().__init__()

        self._api = config['apiBaseUrl']
        self._cert = config.get('cert')

        res = requests.post(f'{self._api}/v1/auth/approle/login', json={
            'role_id': config['roleId'],
            'secret_id': config['secretId'],
        }, verify=self._cert)
        if res.status_code == 200:
            self._client_token = res.json()['auth']['client_token']
        else:
            raise requests.HTTPError(res.status_code, 'Could not login into Vault', res.content)

    def __kv_get(self, key: str) -> Dict[str, any]:
        res = requests.get(f'{self._api}/v1/{key}', headers={'X-Vault-Token': self._client_token}, verify=self._cert)
        if res.status_code == 200:
            return res.json()
        else:
            raise requests.HTTPError(res.status_code, f'Could not get secret {key}', res.content)

    def get_secret(self, key: str) -> str:
        split = key.split('#')
        if len(split) != 2:
            split += 'value'
        return self.__kv_get(split[0])['data'][split[1]]

    def get_provider(self, key: str) -> Dict[str, any]:
        return self.__kv_get(key)['data']

    def __del__(self):
        requests.post(f'{self._api}/v1/auth/token/revoke-self', headers={'X-Vault-Token': self._client_token},
                      verify=self._cert)
        self._client_token = None
