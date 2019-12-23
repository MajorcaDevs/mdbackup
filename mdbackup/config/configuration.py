import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from mdbackup.config.cloud import CloudConfig
from mdbackup.config.secret import SecretConfig
from mdbackup.jsonschemavalidator import validate
from mdbackup.utils import read_data_file


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
        if isinstance(path, dict):
            parsed_config = path
        else:
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
                    'Expected a config file config.json, config.yaml or config.yml, but none of them was found',
                )

            parsed_config = read_data_file(self.__file)
            if parsed_config is None:
                raise NotImplementedError(f'Cannot read this type of config file: {self.__file.parts[-1]}')

        schema_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            '..',
            'json-schemas',
            'config.schema.json',
        )
        if not validate(schema_path, parsed_config):
            raise Exception('Configuration is invalid')

        self._parse_config(parsed_config)

    def _parse_config(self, conf):
        self.__backups_path = Path(conf['backupsPath'])
        self.__actions_modules = conf.get('actionsModules', [])
        self.__log_level = logging.getLevelName(conf.get('logLevel', 'WARNING'))
        self.__max_backups_kept = conf.get('maxBackupsKept', 7)
        self.__env = conf.get('env', {})
        self.__secrets = [
            SecretConfig(key, secret_dict.get('envDefs'), secret_dict['config'], secret_dict.get('storageProviders'))
            for key, secret_dict in conf.get('secrets', {}).items()
        ]
        self.__hooks = conf.get('hooks', {})
        self.__cloud = CloudConfig(conf.get('cloud', {'providers': []}))

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
    def secrets(self) -> List[SecretConfig]:
        """
        :return: The list of secret backend configurations from where some config will be obtained securely
        """
        return self.__secrets

    @property
    def cloud(self) -> CloudConfig:
        """
        :return: The cloud configuraiton
        """
        return self.__cloud

    @property
    def hooks(self) -> Dict[str, str]:
        """
        :return: The hooks dictionary
        """
        return self.__hooks
