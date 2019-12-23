from ftplib import FTP, FTP_TLS
import logging
from pathlib import Path
from typing import List, Union

from mdbackup.config import StorageConfig
from mdbackup.storage.storage import AbstractStorage


class FTPStorage(AbstractStorage):
    def __init__(self, params: StorageConfig):
        self.__log = logging.getLogger(f'{__name__}:FTPStorage')
        self.__conn = self._create_connection(params)

        self.__conn.port = params.get('port', 21)
        self.__conn.cwd(params.backups_path)
        self.__dir = Path(params.backups_path)

    def __del__(self):
        if hasattr(self, '_FTPStorage__conn') or hasattr(self, '_FTPSStorage__conn'):
            self.__log.debug('Closing connection')
            self.__conn.close()

    def _create_connection(self, params: StorageConfig):
        self.__log.debug('Creating connection to FTP server ' + params['host'])
        return FTP(host=params['host'],
                   user=params.get('user'),
                   passwd=params.get('password'),
                   acct=params.get('acct'))

    def list_directory(self, path: Union[str, Path]) -> List[str]:
        self.__log.debug(f'Retrieving contents of directory {path}')
        return [str(filename) for (filename, _) in self.__conn.mlsd(str(self.__dir / path))][2:]

    def create_folder(self, name: str, parent: Union[Path, str] = '.') -> str:
        path = self.__dir / parent
        self.__conn.cwd(str(path))
        if name not in self.list_directory(parent):
            self.__log.info(f'Creating folder "{path / name}"')
            self.__conn.mkd(name)
        else:
            self.__log.debug(f'Folder "{path / name}"" already exists')
        return str((path / name).relative_to(self.__dir))

    def upload(self, path: Path, parent: Union[Path, str] = '.'):
        dir_path = self.__dir / parent
        self.__conn.cwd(str(dir_path))
        with open(str(path), 'rb') as file_to_upload:
            self.__log.info(f'Uploading file {path} to {parent}')
            self.__conn.storbinary(f'STOR {path.name}', file_to_upload)

    def delete(self, path: Union[Path, str]):
        path = self.__dir / path
        is_dir = False
        self.__log.info(f'Deleting {path}')
        for (name, properties) in self.__conn.mlsd(path=str(path)):
            if name in ['.', '..']:
                is_dir = True
                continue
            elif properties['type'] == 'file':
                self.__conn.delete(str(path / name))
            elif properties['type'] == 'dir':
                self.delete(str(path / name))
        self.__conn.rmd(str(path)) if is_dir else None


class FTPSStorage(FTPStorage):
    def __init__(self, params: StorageConfig):
        super().__init__(params)
        self.__log = logging.getLogger(f'{__name__}:FTPSStorage')

    def _create_connection(self, params: StorageConfig):
        self.__log.debug('Creating connection to FTPS server ' + params['host'])
        return FTP_TLS(host=params['host'],
                       user=params.get('user'),
                       passwd=params.get('password'),
                       acct=params.get('acct'),
                       keyfile=params.get('keyFile'),
                       certfile=params.get('certFile'))
