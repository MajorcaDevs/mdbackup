from enum import Enum
from typing import Optional

from mdbackup.storage.drive import GDriveStorage
from mdbackup.storage.s3 import S3Storage
from mdbackup.storage.storage import AbstractStorage, T


class StorageImplementation(Enum):
    GDrive = GDriveStorage
    S3 = S3Storage


def create_storage_instance(params) -> Optional[AbstractStorage[T]]:
    try:
        impl = next((impl.value for impl in StorageImplementation if impl.name.lower() == params.type.lower()))
        return impl(params)
    except StopIteration:
        return None
