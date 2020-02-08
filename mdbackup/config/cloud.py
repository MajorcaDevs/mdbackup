from typing import Any, Dict, List, Optional

from mdbackup.config.storage import StorageConfig
from mdbackup.utils import change_keys


class CloudConfig(object):
    def __init__(self, conf: Dict[str, str]):
        self.__providers = [StorageConfig(provider_dict) for provider_dict in conf['providers']]
        if 'compression' in conf:
            self.__compression_level = conf['compression'].get('level', 6)
            self.__compression_strategy = conf['compression']['method']
            self.__compression_cpus = conf['compression'].get('cpus', None)
        else:
            self.__compression_level = None
            self.__compression_strategy = None
            self.__compression_cpus = None
        if 'encrypt' in conf:
            self.__cypher_strategy = conf['encrypt']['strategy']
            self.__cypher_params = change_keys(conf['encrypt'])
            del self.__cypher_params['strategy']
        else:
            self.__cypher_strategy = None
            self.__cypher_params = None

    @property
    def providers(self) -> List[StorageConfig]:
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

    @property
    def compression_cpus(self) -> Optional[int]:
        """
        :return: The threads/cpus to use during compression
        """
        return self.__compression_cpus

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
