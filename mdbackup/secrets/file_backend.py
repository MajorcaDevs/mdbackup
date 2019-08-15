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

import json
from pathlib import Path
from typing import Dict

try:
    try:
        from yaml import CLoader as Loader, load as yaml_load
    except ImportError:
        from yaml import Loader, load as yaml_load
except ImportError:
    yaml_load = None
    Loader = None

from mdbackup.secrets.secrets import AbstractSecretsBackend


class FileSecretsBackend(AbstractSecretsBackend):
    def __init__(self, config: Dict[str, any]):
        super().__init__()

        self._base_path = Path(config['basePath']) if 'basePath' in config else None

    def get_secret(self, key: str) -> str:
        path = Path(key)
        if not path.is_absolute():
            path = self._base_path / path
        with open(path, 'r') as secret_file:
            lines = secret_file.readlines()
            contents = [line.replace('\r\n', '').replace('\n', '') for line in lines]
            while len(contents[-1]) == 0:
                contents.pop()
        return '\n'.join(contents)

    def get_provider(self, key: str) -> Dict[str, any]:
        contents = self.get_secret(key)
        if key.endswith('.yaml') or key.endswith('.yml'):
            if yaml_load is None:
                raise ImportError('In order to use yaml files, install pyyaml package: pip install pyyaml')
            return yaml_load(contents, Loader=Loader)
        return json.loads(contents)
