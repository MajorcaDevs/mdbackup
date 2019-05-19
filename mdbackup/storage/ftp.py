# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2019  Melchor Alejo Garau Madrigal & Andrés Mateos García
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

from ftplib import FTP, FTP_TLS
import logging
from pathlib import Path
from typing import List, Union

from mdbackup.config import ProviderConfig
from mdbackup.storage.storage import AbstractStorage


class FTPStorage(AbstractStorage[Path]):
    def __init__(self, params: ProviderConfig):
        self.__log = logging.getLogger(f'{__name__}:FTPStorage')
        self.__conn = self._create_connection(params)

        self.__conn.cwd(params.backups_path)
        self.__dir = Path(params.backups_path)

    def __del__(self):
        if hasattr(self, '_FTPStorage__conn') or hasattr(self, '_FTPSStorage__conn'):
            self.__log.debug('Closing connection')
            self.__conn.close()

    def _create_connection(self, params: ProviderConfig):
        self.__log.debug('Creating connection to FTP server ' + params['host'])
        return FTP(host=params['host'],
                   user=params.get('user'),
                   passwd=params.get('password'),
                   acct=params.get('acct'))

    def list_directory(self, path: Union[str, Path]) -> List[Path]:
        self.__log.debug(f'Retrieving contents of directory {path}')
        return [filename for (filename, _) in self.__conn.mlsd(self.__dir / path)][2:]

    def create_folder(self, name: str, parent: Union[Path, str] = None) -> Path:
        path = self.__dir / parent
        self.__conn.cwd(str(path))
        if name not in self.list_directory(parent):
            self.__log.info(f'Creating folder "{path / name}"')
            self.__conn.mkd(name)
        else:
            self.__log.debug(f'Folder "{path / name}"" already exists')
        return path / name

    def upload(self, path: Path, parent: Union[Path, str] = None):
        dir_path = self.__dir / parent
        self.__conn.cwd(str(dir_path))
        with open(path, 'rb') as file_to_upload:
            self.__log.info(f'Uploading file {path} to {parent}')
            self.__conn.storbinary(f'STOR {path.name}', file_to_upload)


class FTPSStorage(FTPStorage):
    def __init__(self, params: ProviderConfig):
        super().__init__(params)
        self.__log = logging.getLogger(f'{__name__}:FTPSStorage')

    def _create_connection(self, params: ProviderConfig):
        self.__log.debug('Creating connection to FTPS server ' + params['host'])
        return FTP_TLS(host=params['host'],
                       user=params.get('user'),
                       passwd=params.get('password'),
                       acct=params.get('acct'),
                       keyfile=params.get('keyFile'),
                       certfile=params.get('certFile'))