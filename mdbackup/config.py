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
from typing import Dict, List, Optional, Tuple

class ProviderConfig(object):
    def __init__(self, provider_dict):
        self.__type = provider_dict['type']
        self.__backups_path = provider_dict['backupsPath']
        self.__client_secrets = provider_dict.get('clientSecrets')
        self.__auth_tokens = provider_dict.get('authTokens')

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

    @property
    def client_secrets(self) -> Optional[str]:
        """
        :return: If needed, a client tokens or a path to a file to them for the cloud provider.
        """
        return self.__client_secrets

    @property
    def auth_tokens(self) -> Optional[str]:
        """
        :return: If needed, a authentication tokens or a path to a file to them for the cloud provider.
        """
        return self.__auth_tokens


class Config(object):
    """
    The configuration object. Retreives any configuration of the system from many different places.

    The main configuration lies on a ``config.json`` file, but parts of the configuration, like environment variables
    or credentials, can be stored in different places, for security reasons.
    """

    def __init__(self, path: Path):
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
        self.__providers = self._parse_providers(conf.get('providers'))
        if 'compression' in conf:
            self.__compression_level = conf['compression'].get('level', 5)
            self.__compression_strategy = conf['compression']['strategy']
        else:
            self.__compression_level = None
            self.__compression_strategy = None

        Config.__check_paths(self.__backups_path)
        Config.__check_paths(self.__custom_utils_script)

    def _parse_providers(self, providers):
        if providers is None:
            return []

        return [ProviderConfig(provider_dict) for provider_dict in providers]

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
