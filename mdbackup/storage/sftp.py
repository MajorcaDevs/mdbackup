import logging
from pathlib import Path
import stat
from typing import List, Union

from paramiko import (
    AutoAddPolicy,
    PKey,
    RejectPolicy,
    SFTPClient,
    SSHClient,
    WarningPolicy,
)

from mdbackup.config import StorageConfig
from mdbackup.storage.storage import AbstractStorage


class SFTPStorage(AbstractStorage):
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
        if 'enableHostKeys' not in params or params['enableHostKeys']:
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

    def list_directory(self, path: Union[str, Path]) -> List[str]:
        path = self.__dir / path
        self.__log.debug(f'Retrieving contents of directory {path}')
        return self.__conn.listdir(str(path))

    def create_folder(self, name: str, parent: Union[Path, str] = '.') -> str:
        path = self.__dir / parent
        self.__conn.chdir(str(path))
        if name not in self.list_directory(parent):
            self.__log.info(f'Creating folder "{path / name}"')
            self.__conn.mkdir(name)
        else:
            self.__log.debug(f'Folder "{path / name}"" already exists')
        return str((path / name).relative_to(self.__dir))

    def upload(self, path: Path, parent: Union[Path, str] = '.'):
        dir_path = self.__dir / parent
        self.__conn.chdir(str(dir_path))
        self.__log.info(f'Uploading file {path} to {parent}')
        self.__conn.put(str(path), path.name, confirm=True)

    def delete(self, path: Union[Path, str]):
        path = self.__dir / path
        path_stats = self.__conn.stat(str(path))
        self.__log.info(f'Deleting {path}')
        if stat.S_ISDIR(path_stats.st_mode):
            entries_in_dir = self.__conn.listdir(str(path))
            for entry in entries_in_dir:
                self.delete(path / entry)
            self.__conn.rmdir(str(path))
        else:
            self.__conn.unlink(str(path))
