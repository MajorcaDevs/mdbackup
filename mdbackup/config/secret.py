from typing import Dict, List, Optional, Union


class SecretConfig(object):
    def __init__(self, secret_type: str, secret_env: Optional[Dict[str, str]], secret_config: Dict[str, any],
                 secret_storage: Optional[List[str]]):
        self.__type = secret_type
        self.__config = secret_config
        self.__env = secret_env if secret_env is not None else {}
        self.__storage = secret_storage if secret_storage is not None else []

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
    def storage(self) -> List[Union[str, Dict[str, str]]]:
        return self.__storage
