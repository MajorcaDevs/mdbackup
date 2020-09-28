from typing import Any, Dict, List, Optional, Union

from mdbackup.secrets import get_secret_backend_implementation


class SecretConfig(object):
    def __init__(self, secret_type: str, secret_env: Optional[Dict[str, str]], secret_config: Dict[str, any],
                 secret_storage: Optional[List[str]]):
        self.__type = secret_type
        self.__config = secret_config
        self.__env = secret_env if secret_env is not None else {}
        self.__storage = secret_storage if secret_storage is not None else []
        self.__backend = get_secret_backend_implementation(self.__type, self.__config)

    @property
    def type(self) -> str:
        return self.__type

    @property
    def backend(self):
        return self.__backend

    @property
    def env(self) -> Dict[str, str]:
        return self.__env

    @property
    def storage(self) -> List[Union[str, Dict[str, str]]]:
        return self.__storage

    @property
    def config(self) -> Dict[str, Any]:
        return self.__config
