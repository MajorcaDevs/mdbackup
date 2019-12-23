import logging
import os
from pathlib import Path
from typing import List, Union

import magic
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive, GoogleDriveFile

from mdbackup.storage.storage import AbstractStorage


class GDriveStorage(AbstractStorage):

    def __init__(self, params):
        """
        Creates an instance of the Google Drive storage. If ``client_secrets``
        is not null, will be used that path to look for the secrets. If
        ``auth_tokens.json`` is not null, will be used that path to store the
        authentication tokens.

        If the authentication tokens doesn't exist, the utility will stop and
        it will show (in the terminal) an URL. That will allow you to log in
        into an account through a browser.
        """
        client_secrets = params.get('clientSecrets', 'config/client_secrets.json')
        auth_tokens = params.get('authTokens', 'config/auth_tokens.json')
        self.__log = logging.getLogger(__name__)
        self.__gauth = GoogleAuth()
        self.__gauth.LoadClientConfigFile(client_secrets)
        if not os.path.exists(auth_tokens):
            self.__gauth.CommandLineAuth()
            self.__gauth.SaveCredentialsFile(auth_tokens)
        else:
            self.__gauth.LoadCredentialsFile(auth_tokens)

        self._drive = GoogleDrive(self.__gauth)
        self.__id_cache = {'/': 'root'}

    def _traverse(self, path: Path, parent_id: str = None, part: int = 0):
        """
        Traverses the path to look for a file or folder in Google Drive. If exists
        will return the GoogleDriveFile, if not, returns None.
        """
        len_parts = len(path.parts)
        if len_parts == part:
            return self._drive.CreateFile({'id': parent_id})

        folder_id = path.parts[part]
        if folder_id == '/':
            if len_parts > 1:
                part += 1
                folder_id = path.parts[part]
            else:
                return self._drive.CreateFile({'id': 'root'})

        if parent_id is None:
            parent_id = 'root'

        sub_path = '/' + '/'.join(path.parts[1:(part+1)])
        if sub_path in self.__id_cache:
            return self._traverse(path, self.__id_cache[sub_path], part + 1)

        file_list = self._drive.ListFile({'q': f"'{parent_id}' in parents and trashed=false"}).GetList()
        for file1 in file_list:
            self.__id_cache[sub_path] = file1['id']
            if file1['title'] == folder_id:
                return self._traverse(path, file1['id'], part + 1)

    def get(self, path):
        """
        Gets the GoogleDriveFile instance for the path specified as argument.
        The path must be a string or Path.
        """
        if isinstance(path, str):
            path = Path(path)
        elif isinstance(path, GoogleDriveFile):
            return path
        elif not isinstance(path, Path):
            raise TypeError('Expected Path or str, received ' + str(type(path)))

        return self._traverse(path)

    def list_directory(self, path: Union[str, Path]) -> List[str]:
        """
        Returns a list of of GoogleDriveFile for the folder in that path.
        The path must exist and must be a directory.
        """
        if isinstance(path, Path) or isinstance(path, str):
            drive_file = self.get(path)
            if drive_file is None:
                raise FileNotFoundError(str(path))
        elif isinstance(path, GoogleDriveFile):
            drive_file = path
        else:
            raise TypeError('Expected Path, str or GoogleDriveFile, received ' + str(type(path)))

        if drive_file.metadata is None or drive_file.metadata == {}:
            drive_file.FetchMetadata()
        if drive_file.metadata['mimeType'] != 'application/vnd.google-apps.folder':
            raise NotADirectoryError(drive_file.metadata['mimeType'])

        files = self._drive.ListFile({'q': f"'{drive_file.metadata['id']}' in parents and trashed=false"}).GetList()
        return [str(Path(path, f.metadata['title'])) for f in files]

    def create_folder(self, name: str, parent: Union[Path, str] = None) -> str:
        """
        Creates a folder with name ``name`` in the root folder or in the
        folder specified in ``parent``. Returns the GoogleDriveFile instance
        for the folder.
        """
        parent_drive = self.get(parent if parent is not None else '/')
        if parent_drive is None:
            raise FileNotFoundError(parent)

        dir1 = self._drive.CreateFile({
            'title': name,
            'parents': [{'id': parent_drive['id']}],
            'mimeType': 'application/vnd.google-apps.folder',
        })
        self.__log.info(f'Creating folder {name} [parent "{parent_drive.metadata["title"]}" {parent_drive["id"]}]')
        dir1.Upload()
        return str(Path(parent, name))

    def upload_file(self, file_path: Path, parent: GoogleDriveFile = None):
        """
        Uploads a file to google drive, in the root folder or in the
        folder specified in ``parent``.
        """
        if parent is None:
            parent = self.get('/')
        elif not isinstance(parent, GoogleDriveFile):
            parent = self.get(parent)
        if parent is None:
            raise FileNotFoundError(parent)

        if isinstance(file_path, str):
            file_path = Path(file_path)
        elif not isinstance(file_path, Path):
            raise TypeError('Expected file path to be a str or Path, received ' + str(type(file_path)))

        mime_type = magic.from_file(str(file_path), mime=True)
        if mime_type == 'inode/x-empty':
            mime_type = 'application/octet-stream'
        if file_path.stat().st_size == 0:
            return

        file1 = self._drive.CreateFile({
            'title': file_path.parts[-1],
            'mimeType': mime_type,
            'parents': [{'id': parent['id']}],
        })
        self.__log.info(f'Uploading file {file_path} with attributes {file1.items()} '
                        f'[parent "{parent.metadata["title"]}" {parent["id"]}]')
        file1.SetContentFile(file_path)
        file1.Upload()

    def upload(self, path, parent=None):
        """
        Uploads something to Google Drive.
        """
        if parent is None:
            parent = self.get('/')
        elif not isinstance(parent, GoogleDriveFile):
            parent = self.get(parent)

        if isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            raise TypeError('Expected file path to be a str or Path, received ' + str(type(path)))

        if path.is_dir():
            new_parent = self.create_folder(path.parts[-1], parent)
            for child_file in path.iterdir():
                self.upload(child_file, new_parent)
        elif path.is_file():
            self.upload_file(path, parent)

    def delete(self, path: Union[Path, str, GoogleDriveFile]):
        if isinstance(path, Path):
            drive_file = self.get(path)
        elif isinstance(path, str):
            drive_file = self.get(Path(path))
        else:
            drive_file = path
        drive_file.Trash()
