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

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from mdbackup.config.secret import SecretConfig
from mdbackup.config.storage import StorageConfig
from mdbackup.utils import change_keys, read_data_file


class Config(object):
    """
    The configuration object. Retrieves any configuration of the system from many different places.

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
        if not path.is_dir():
            raise NotADirectoryError(f'"{path}" must be a directory')

        self.config_folder = path
        if (path / 'config.json').exists():
            self.__file = path / 'config.json'
        elif (path / 'config.yaml').exists():
            self.__file = path / 'config.yaml'
        elif (path / 'config.yml').exists():
            self.__file = path / 'config.yml'
        else:
            raise FileNotFoundError(
                'Expected a config file config.json, config.yaml or config.yml, but non of them was found',
            )

        parsed_config = read_data_file(self.__file)
        if parsed_config is None:
            raise NotImplementedError(f'Cannot read this type of config file: {self.__file.parts[-1]}')

        self._parse_config(parsed_config)

    def _parse_config(self, conf):
        self.__backups_path = Path(conf['backupsPath'])
        self.__actions_modules = conf.get('actionsModules', [])
        self.__log_level = logging.getLevelName(conf.get('logLevel', 'WARNING'))
        self.__max_backups_kept = conf.get('maxBackupsKept', 7)
        self.__env = conf.get('env', {})
        self.__providers = [StorageConfig(provider_dict) for provider_dict in conf.get('storage', [])]
        self.__secrets = [
            SecretConfig(key, secret_dict.get('envDefs'), secret_dict['config'], secret_dict.get('storage'))
            for key, secret_dict in conf.get('secrets', {}).items()
        ]
        self.__hooks = conf.get('hooks', {})
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

        Config.__check_paths('backupsPath', self.__backups_path)

    @staticmethod
    def __check_paths(field: str, path: Optional[Path]):
        if path is None:
            return
        if not path.exists():
            raise FileNotFoundError(f'{field}: "{path}" must exist')
        if not path.is_dir():
            raise NotADirectoryError(f'{field}: "{path}" must be a directory')

    def __del__(self):
        pass

    @property
    def backups_path(self) -> Path:
        """
        :return: The path where the backups are stored.
        """
        return self.__backups_path

    @property
    def actions_modules(self) -> List[str]:
        """
        :return: Defines a list of python modules that contains extra action implementations
        """
        return self.__actions_modules

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
    def providers(self) -> List[StorageConfig]:
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

    @property
    def hooks(self) -> Dict[str, str]:
        """
        :return: The hooks dictionary
        """
        return self.__hooks
