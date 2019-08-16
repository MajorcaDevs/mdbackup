from typing import Optional

from mdbackup.check_packages import (
    check,
    check_b2sdk,
    check_boto3,
    check_magic,
    check_paramiko,
    check_pydrive,
)
from mdbackup.storage.storage import AbstractStorage


@check('BackBlaze cloud storage', check_b2sdk, check_magic)
def load_backblaze_storage():
    from mdbackup.storage.backblaze import B2Storage
    return B2Storage


@check('Google Drive cloud storage', check_pydrive, check_magic)
def load_gdrive_storage():
    from mdbackup.storage.drive import GDriveStorage
    return GDriveStorage


@check('any S3 cloud storage', check_boto3, check_magic)
def load_s3_storage():
    from mdbackup.storage.s3 import S3Storage
    return S3Storage


@check('FTP storage')
def load_ftp_storage(secure):
    from mdbackup.storage.ftp import FTPStorage, FTPSStorage
    return FTPSStorage if secure else FTPStorage


@check('SFTP storage', check_paramiko)
def load_sftp_storage():
    from mdbackup.storage.sftp import SFTPStorage
    return SFTPStorage


__impls = {
    'gdrive': load_gdrive_storage,
    's3': load_s3_storage,
    'b2': load_backblaze_storage,
    'ftp': lambda: load_ftp_storage(False),
    'ftps': lambda: load_ftp_storage(True),
    'sftp': load_sftp_storage,
}


def create_storage_instance(params) -> Optional[AbstractStorage]:
    try:
        impl = __impls[params.type.lower()]
    except KeyError:
        return None
    return impl()(params)
