# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
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
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from mdbackup.utils import change_keys


class ProviderConfig(object):
    def __init__(self, provider_dict: Dict[str, str]):
        self.__type = provider_dict['type']
        self.__backups_path = provider_dict['backupsPath']
        self.__extra = {key: value for key, value in provider_dict.items() if key not in ('type', 'backupsPath')}

    @property
    def type(self) -> str:
        """
        :return: The cloud provider.
        """
        return self.__type

    @property
    def backups_path(self) -> str:
        """
        :return: The path where the backups will be stored in the cloud
        """
        return self.__backups_path

    def __getitem__(self, key: str):
        return self.__extra[key]

    def get(self, key: str, default=None):
        return self.__extra.get(key, default)


class SecretConfig(object):
    def __init__(self, secret_type: str, secret_env: Optional[Dict[str, str]], secret_config: Dict[str, any],
                 secret_providers: Optional[List[str]]):
        self.__type = secret_type
        self.__config = secret_config
        self.__env = secret_env if secret_env is not None else {}
        self.__providers = secret_providers if secret_providers is not None else []

    @property
    def type(self) -> str:
        return self.__type

    @property
    def config(self) -> Dict[str, any]:
        return self.__config

    @property
    def env(self) -> Dict[str, str]:
        return self.__env

    @property
    def providers(self) -> List[str]:
        return self.__providers


class Config(object):
    """
    The configuration object. Retreives any configuration of the system from many different places.

    The main configuration lies on a ``config.json`` file, but parts of the configuration, like environment variables
    or credentials, can be stored in different places, for security reasons.
    """

    def __init__(self, path: Union[Path, str, bytes]):
        """
        Creates an instance of the configuration with the given ``config.json``
        """
        if not isinstance(path, Path):
            path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f'"{path}" must exist')
        if not path.is_file():
            raise IsADirectoryError(f'"{path}" must be a file')

        self.__file = path
        with open(path) as config_file:
            self._parse_config(json.load(config_file))

    def _parse_config(self, conf):
        self.__backups_path = Path(conf['backupsPath'])
        self.__custom_utils_script = Path(conf['customUtilsScript']) if 'customUtilsScript' in conf else None
        self.__log_level = logging.getLevelName(conf.get('logLevel', 'WARNING'))
        self.__max_backups_kept = conf.get('maxBackupsKept', 7)
        self.__env = conf.get('env', {})
        self.__providers = [ProviderConfig(provider_dict) for provider_dict in conf.get('providers', [])]
        self.__secrets = [SecretConfig(key, secret_dict.get('env'), secret_dict['config'], secret_dict.get('providers'))
                          for key, secret_dict in conf.get('secrets', {}).items()]
        if 'compression' in conf:
            self.__compression_level = conf['compression'].get('level', 5)
            self.__compression_strategy = conf['compression']['strategy']
        else:
            self.__compression_level = None
            self.__compression_strategy = None
        if 'cypher' in conf:
            self.__cypher_strategy = conf['cypher']['strategy']
            self.__cypher_params = change_keys(conf['cypher'])
            del self.__cypher_params['strategy']
        else:
            self.__cypher_strategy = None
            self.__cypher_params = None

        Config.__check_paths(self.__backups_path)
        Config.__check_paths(self.__custom_utils_script)

    @staticmethod
    def __check_paths(path: Path):
        if path is None:
            return
        if not path.exists():
            raise FileNotFoundError(f'"{path}" must exist')
        if not path.is_dir():
            raise NotADirectoryError(f'"{path}" must be a directory')

    @property
    def backups_path(self) -> Path:
        """
        :return: The path where the backups are stored.
        """
        return self.__backups_path

    @property
    def custom_utils_script(self) -> Optional[Path]:
        """
        :return: If defined, this file will be included when the steps are going to run.
        """
        return self.__custom_utils_script

    @property
    def log_level(self) -> int:
        """
        :return: The log level for the logs
        """
        return self.__log_level

    @property
    def max_backups_kept(self) -> int:
        """
        :return: The maximum number of backups to keep
        """
        return self.__max_backups_kept

    @property
    def env(self) -> Dict[str, str]:
        """
        :return: The environment variables that will be injected into every step
        """
        return self.__env

    @property
    def providers(self) -> List[ProviderConfig]:
        """
        :return: The list of cloud providers where the backups will be uploaded
        """
        return self.__providers

    @property
    def secrets(self) -> List[SecretConfig]:
        """
        :return: The list of secret backend configurations from where some config will be obtained securely
        """
        return self.__secrets

    @property
    def compression_strategy(self) -> Optional[str]:
        """
        :return: The compression strategy
        """
        return self.__compression_strategy

    @property
    def compression_level(self) -> Optional[int]:
        """
        :return: The compression level
        """
        return self.__compression_level

    @property
    def cypher_strategy(self) -> Optional[str]:
        """
        :return: The cypher strategy
        """
        return self.__cypher_strategy

    @property
    def cypher_params(self) -> Optional[Dict[str, Any]]:
        """
        :return: The cypher parameters for the given strategy
        """
        return self.__cypher_params
