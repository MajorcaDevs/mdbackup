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
from typing import List, Union

import boto3
import magic

from mdbackup.storage.storage import AbstractStorage


class S3Storage(AbstractStorage):

    def __init__(self, config):
        self.__log = logging.getLogger(__name__)
        self.__s3 = boto3.client(
            's3',
            region_name=config['region'],
            endpoint_url=config.get('endpoint'),
            aws_access_key_id=config['accessKeyId'],
            aws_secret_access_key=config['accessSecretKey'],
        )

        self.__bucket: str = config['bucket']
        self.__storageclass: str = config.get('storageClass', 'STANDARD')
        self.__pre = config.backups_path if not config.backups_path.endswith('/') else config.backups_path[:-1]
        self.__pre = self.__pre if not self.__pre.startswith('/') else self.__pre[1:]

    def list_directory_recursive(self, path: Union[str, Path]) -> List[str]:
        path = path if isinstance(path, str) else str(path)
        if path.startswith('/'):
            path = path[1:]
        full_path = f'{self.__pre}/{path}'
        items = [key
                 for key in [item['Key'].replace(f'{self.__pre}/', '')
                             for item in self.__s3.list_objects_v2(Bucket=self.__bucket, Prefix=full_path)['Contents']]
                 if key != '']
        return items

    def list_directory(self, path: Union[str, Path]) -> List[str]:
        items = self.list_directory_recursive(path)
        rep_path = path + '/' if path != '' else path
        items = [key for key in items
                 if (len(key.replace(rep_path, '').split('/')) == 2 if key.endswith('/')
                     else len(key.replace(rep_path, '').split('/')) == 1)]
        return items

    def create_folder(self, name: str, parent: Union[Path, str, str] = None) -> str:
        parent = parent if parent is not None else ''
        parent = parent[:-1] if parent.endswith('/') else parent
        name = f'{name}/' if not name.endswith('/') else name
        key = f'{parent}/{name}'
        if key.startswith('/'):
            key = key[1:]
        key = f'{self.__pre}/{key}'
        self.__log.info(f'Creating folder {key}')
        ret = self.__s3.put_object(Key=key, Bucket=self.__bucket)
        self.__log.debug(ret)
        return key.replace(f'{self.__pre}/', '')

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
        if key.startswith('/'):
            key = key[1:]
        key = f'{self.__pre}/{key}'
        self.__log.info(f'Uploading file {key} (from {path})')
        ret = self.__s3.upload_file(str(path.absolute()),
                                    self.__bucket,
                                    key,
                                    ExtraArgs={
                                        'ContentType': magic.from_file(str(path.absolute()), mime=True),
                                        'StorageClass': self.__storageclass,
                                    })
        self.__log.debug(ret)

    def delete(self, path: Union[Path, str]):
        path = str(path)
        if path.startswith('/'):
            path = path[1:]
        self.__log.info(f'Deleting {self.__pre}/{path}')
        objects_to_delete = self.list_directory_recursive(path)[::-1]
        while len(objects_to_delete) > 0:
            ret = self.__s3.delete_objects(
                Bucket=self.__bucket,
                Delete={
                    'Objects': [{'Key': f'{self.__pre}/{key}'} for key in objects_to_delete],
                    'Quiet': True,
                },
            )

            self.__log.debug(ret)
            objects_to_delete = self.list_directory_recursive(path)[::-1]
