from typing import Dict, Optional


class StorageConfig(object):
    def __init__(self, provider_dict: Dict[str, str]):
        self.__type = provider_dict['type']
        self.__backups_path = provider_dict['backupsPath']
        self.__max_backups_kept = provider_dict.get('maxBackupsKept', None)
        self.__extra = {key: value
                        for key, value in provider_dict.items()
                        if key not in ('type', 'backupsPath', 'maxBackupsKept')}

    @property
    def type(self) -> str:
        """
        :return: The storage provider.
        """
        return self.__type

    @property
    def backups_path(self) -> str:
        """
        :return: The path where the backups will be stored in the storage provider.
        """
        return self.__backups_path

    @property
    def max_backups_kept(self) -> Optional[int]:
        """
        :return: The maximum number of backups to keep in this provider. If the value is None, no cleanup must be done.
        """
        return self.__max_backups_kept

    def __contains__(self, item: str):
        return item in self.__extra

    def __getitem__(self, key: str):
        return self.__extra[key]

    def get(self, key: str, default=None):
        return self.__extra.get(key, default)
