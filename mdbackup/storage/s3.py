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
from typing import Union, List

import boto3

from mdbackup.storage.storage import AbstractStorage


class S3Storage(AbstractStorage[str]):

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

    def list_directory(self, path: Union[str, Path, str]) -> List[str]:
        return [item['Key'] for item in self.__s3.list_objects_v2(Bucket=self.__bucket)['Contents']]

    def create_folder(self, name: str, parent: Union[Path, str, str]=None) -> str:
        key = f'{parent.absolute()}/{name}/'
        self.__log.info(f'Creating folder {key}')
        ret = self.__s3.put_object(Key=f'{parent.absolute()}/{name}/', Bucket='mds3')
        self.__log.debug(ret)
        return key

    def upload(self, path: Path, parent: Union[Path, str, str]=None):
        if isinstance(parent, Path):
            key = f'{parent.absolute()}/{path.name}'
        elif isinstance(parent, str):
            key = f'{parent}/{path.name}'
        else:
            key = path.name
        self.__log.info(f'Uploading file {key} (from {path})')
        ret = self.__s3.upload_file(str(path.absolute()), self.__bucket, key)
        self.__log.debug(ret)
