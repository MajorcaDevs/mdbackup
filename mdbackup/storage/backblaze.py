import logging
from pathlib import Path
from typing import List, Union

from b2sdk.account_info.in_memory import InMemoryAccountInfo
from b2sdk.api import B2Api, Bucket
import magic

from mdbackup.storage.storage import AbstractStorage


class B2Storage(AbstractStorage):

    def __init__(self, config):
        self.__log = logging.getLogger(__name__)
        self.__info = InMemoryAccountInfo()
        self.__b2_api = b2_api = B2Api(self.__info)
        self.__b2 = b2_api.authorize_account("production",
                                             application_key_id=config['keyId'],
                                             application_key=config['appKey'])
        self.__bucket: Bucket = self.__b2_api.get_bucket_by_name(config['bucket'])
        self.__password: str = config.get('password')
        self.__pre = config.backups_path if not config.backups_path.endswith('/') else config.backups_path[:-1]
        self.__pre = self.__pre.lstrip('/') if self.__pre is not None else ''

    def __ok_key(self, path: Union[str, Path]):
        path = str(path).lstrip('/')

        if self.__pre != '':
            path = f'{self.__pre}/{path}'

        path = path.rstrip('/')
        return path

    def list_directory(self, path: Union[str, Path, str]) -> List[str]:
        full_path = self.__ok_key(path)
        return [key[len(self.__pre):].lstrip('/')
                for key in [file_name[len(self.__pre):].lstrip('/')
                            for (_, file_name) in self.__bucket.list_file_names(full_path)]
                if key != '']

    def create_folder(self, name: str, parent: Union[Path, str] = None) -> str:
        parent = parent.strip('/') if parent is not None else ''
        key = self.__ok_key(f'{parent}/{name}') + '/'
        return key[len(self.__pre):].lstrip('/')

    def upload(self, path: Path, parent: Union[Path, str] = None):
        if isinstance(parent, Path):
            key = '/'.join(parent.absolute().parts + (path.name,))
        elif isinstance(parent, str):
            if parent.endswith('/'):
                key = (parent + path.name)
            else:
                key = f'{parent}/{path.name}'
        else:
            key = path.name
        key = self.__ok_key(key)
        self.__log.info(f'Uploading file {key} (from {path})')
        file_to_upload = str(path.absolute())
        ret = self.__bucket.upload_local_file(local_file=file_to_upload,
                                              file_name=key,
                                              content_type=magic.from_file(str(path.absolute()), mime=True),
                                              )
        self.__log.debug(ret)

    def delete(self, path: Union[Path, str]):
        full_path = self.__ok_key(path)
        self.__log.info(f'Deleting {full_path}')
        objects_to_delete = self.__bucket.ls(full_path, recursive=True)
        for (info, key) in objects_to_delete:
            ret = self.__bucket.delete_file_version(file_id=info.id_, file_name=key)
            self.__log.debug(ret)
