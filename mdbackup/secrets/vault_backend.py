# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2019  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Dict

import requests

from mdbackup.secrets.secrets import AbstractSecretsBackend


class VaultSecretsBackend(AbstractSecretsBackend):
    def __init__(self, config: Dict[str, any]):
        super().__init__()

        self._api = config['apiBaseUrl']

        res = requests.post(f'{self._api}/v1/auth/approle/login', json={
            'role_id': config['roleId'],
            'secret_id': config['secretId'],
        })
        if res.status_code == 200:
            self._client_token = res.json()['auth']['client_token']
        else:
            raise requests.HTTPError(res.status_code, 'Could not login into Vault', res.content)

    def __kv_get(self, key: str) -> Dict[str, any]:
        res = requests.get(f'{self._api}/v1/{key}', headers={'X-Vault-Token': self._client_token})
        if res.status_code == 200:
            return res.json()
        else:
            raise requests.HTTPError(res.status_code, f'Could not get secret {key}', res.content)

    def get_secret(self, key: str) -> str:
        split = key.split('#')
        if len(split) != 2:
            raise KeyError(f'"{key}" is invalid: expected "backend/path/to/secret#key"')
        return self.__kv_get(split[0])['data'][split[1]]

    def get_provider(self, key: str) -> Dict[str, any]:
        return self.__kv_get(key)['data']
