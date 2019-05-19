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

from paramiko import SSHClient, SFTPClient, PKey, RejectPolicy, AutoAddPolicy, WarningPolicy
import logging
from pathlib import Path
from typing import List, Union

from mdbackup.config import StorageConfig
from mdbackup.storage.storage import AbstractStorage


class SFTPStorage(AbstractStorage[Path]):
    def __init__(self, params: StorageConfig):
        self.__log = logging.getLogger(__name__)
        self.__conn = self._create_connection(params)

        self.__conn.chdir(params.backups_path)
        self.__dir = Path(params.backups_path)

    def __del__(self):
        if hasattr(self, '_SFTPStorage__conn'):
            self.__log.debug('Closing connection')
            self.__conn.close()

    def _create_connection(self, params: StorageConfig) -> SFTPClient:
        self.__log.debug('Creating connection to SSH server ' + params['host'])
        self.__ssh = SSHClient()
        if 'disableHostKeys' not in params or params['disableHostKeys']:
            self.__ssh.load_system_host_keys(filename=params.get('hostKeysFilePath'))

        should_save_host_keys = False
        if 'knownHostsPolicy' in params:
            policy: str = params['knownHostsPolicy'].lower()
            if policy == 'reject':
                self.__ssh.set_missing_host_key_policy(RejectPolicy)
            elif policy == 'auto-add':
                self.__ssh.set_missing_host_key_policy(AutoAddPolicy)
                should_save_host_keys = True
            elif policy == 'ignore':
                self.__ssh.set_missing_host_key_policy(WarningPolicy)

        pkey = None
        if 'privateKey' in params:
            pkey = PKey(data=params['privateKey'])
        self.__ssh.connect(hostname=params['host'],
                           port=params.get('port', 22),
                           username=params.get('user'),
                           password=params.get('password'),
                           pkey=pkey,
                           key_filename=params.get('privateKeyPath'),
                           allow_agent=params.get('allowAgent'),
                           compress=params.get('compress'))

        if should_save_host_keys and 'hostKeysFilePath' in params:
            self.__ssh.save_host_keys(filename=params['hostKeysFilePath'])

        self.__log.debug('Starting SFTP client')
        return self.__ssh.open_sftp()

    def list_directory(self, path: Union[str, Path]) -> List[Path]:
        self.__log.debug(f'Retrieving contents of directory {path}')
        return self.__conn.listdir(path)

    def create_folder(self, name: str, parent: Union[Path, str] = None) -> Path:
        path = self.__dir / parent
        self.__conn.chdir(str(path))
        if name not in self.list_directory(parent):
            self.__log.info(f'Creating folder "{path / name}"')
            self.__conn.mkdir(name)
        else:
            self.__log.debug(f'Folder "{path / name}"" already exists')
        return path / name

    def upload(self, path: Path, parent: Union[Path, str] = None):
        dir_path = self.__dir / parent
        self.__conn.chdir(str(dir_path))
        self.__log.info(f'Uploading file {path} to {parent}')
        self.__conn.put(str(path), path.name, confirm=True)
