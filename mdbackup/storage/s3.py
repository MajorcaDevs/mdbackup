import logging
from pathlib import Path
from typing import List, Union

import boto3
import magic

from mdbackup.storage.storage import AbstractStorage


class S3Storage(AbstractStorage):

    def __init__(self, config):
        self.__log = logging.getLogger(__name__)
        self.__s3 = boto3.client(
            's3',
            region_name=config.get('region'),
            endpoint_url=config.get('endpoint'),
            aws_access_key_id=config['accessKeyId'],
            aws_secret_access_key=config['accessSecretKey'],
        )

        self.__bucket: str = config['bucket']
        self.__storageclass: str = config.get('storageClass', 'STANDARD')
        self.__pre = config.backups_path if not config.backups_path.endswith('/') else config.backups_path[:-1]
        self.__pre = self.__pre.lstrip('/') if self.__pre is not None else ''

    def __ok_key(self, path: Union[str, Path]):
        path = str(path).lstrip('/')

        if self.__pre != '':
            path = f'{self.__pre}/{path}'

        path = path.rstrip('/')
        return path

    def list_directory_recursive(self, path: Union[str, Path]) -> List[str]:
        full_path = self.__ok_key(path)
        res = self.__s3.list_objects_v2(Bucket=self.__bucket, Prefix=full_path)
        items = [key
                 for key in [item['Key'][len(self.__pre):].lstrip('/')
                             for item in res.get('Contents', [])]
                 if key != '']
        return items

    def list_directory(self, path: Union[str, Path]) -> List[str]:
        items = self.list_directory_recursive(path)
        rep_path = path + '/' if path != '' else path
        items = [key.lstrip('/') for key in items
                 if (len(key.replace(rep_path, '').split('/')) == 2 if key.endswith('/')
                     else len(key.replace(rep_path, '').split('/')) == 1)]
        return items

    def create_folder(self, name: str, parent: Union[Path, str, str] = None) -> str:
        parent = parent.strip('/') if parent is not None else ''
        key = self.__ok_key(f'{parent}/{name}') + '/'
        self.__log.info(f'Creating folder {key}')
        ret = self.__s3.put_object(Key=key, Bucket=self.__bucket)
        self.__log.debug(ret)
        return key[len(self.__pre):].lstrip('/')

    def upload(self, path: Path, parent: Union[Path, str, str] = None):
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
        self.__s3.upload_file(str(path.absolute()),
                              self.__bucket,
                              key,
                              ExtraArgs={
                                  'ContentType': magic.from_file(str(path.absolute()), mime=True),
                                  'StorageClass': self.__storageclass,
                              })

    def delete(self, path: Union[Path, str]):
        full_path = self.__ok_key(path)
        self.__log.info(f'Deleting {full_path}')
        objects_to_delete = self.list_directory_recursive(path)[::-1]
        while len(objects_to_delete) > 0:
            self.__s3.delete_objects(
                Bucket=self.__bucket,
                Delete={
                    'Objects': [{'Key': f'{self.__pre}/{key}'} for key in objects_to_delete],
                    'Quiet': True,
                },
            )

            objects_to_delete = self.list_directory_recursive(path)[::-1]
