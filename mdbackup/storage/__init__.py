from typing import Optional

from mdbackup.check_packages import check, check_b2sdk, check_boto3, check_magic, check_pydrive
from mdbackup.storage.storage import AbstractStorage, T


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


def create_storage_instance(params) -> Optional[AbstractStorage[T]]:
    try:
        return {
            'gdrive': load_gdrive_storage,
            's3': load_s3_storage,
            'b2': load_backblaze_storage,
        }[params.type.lower()]()(params)
    except KeyError:
        return None
