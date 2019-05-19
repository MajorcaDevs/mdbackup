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

from b2sdk.api import B2Api
from b2sdk.account_info.in_memory import InMemoryAccountInfo

import magic

from mdbackup.storage.storage import AbstractStorage


class B2Storage(AbstractStorage[str]):

    def __init__(self, config):
        self.__log = logging.getLogger(__name__)
        self.__info = InMemoryAccountInfo()
        self.__b2_api = b2_api = B2Api(self.__info)
        self.__b2 = b2_api.authorize_account("production", application_key_id=config['keyId'], application_key=config['appKey'])
        self.__bucket: bucket = self.__b2_api.get_bucket_by_name(config['bucket'])
        self.__password: str = config.get('password')
        self.__pre = config.backups_path if not config.backups_path.endswith('/') else config.backups_path[:-1]

    def list_directory(self, path: Union[str, Path, str]) -> List[str]:
        path = path if isinstance(path, str) else str(path)
        return [f['fileName'] for f in bucket.list_file_names()['files']]
                if path.startswith('/'):
                    path = path[1:]

    def create_folder(self, name: str, parent: Union[Path, str, str]=None) -> str:
        key = f'{parent}/{name}/'
        if key.startswith('/'):
            key = key[1:]
        return key

    def upload(self, path: Path, parent: Union[Path, str, str]=None):
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
        self.__log.info(f'Uploading file {key} (from {path})')
        file_to_upload = str(path.absolute())
        ret = self.__bucket.upload_local_file(local_file=file_to_upload,
                                             file_name=key,
                                             content_type=magic.from_file(str(path.absolute()), mime=True),
                                            )
        self.__log.debug(ret)
