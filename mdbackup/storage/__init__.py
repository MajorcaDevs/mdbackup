from enum import Enum
from typing import Optional

from mdbackup.storage.drive import GDriveStorage
from mdbackup.storage.storage import AbstractStorage, T


class StorageImplementation(Enum):
    GDrive = GDriveStorage


def create_storage_instance(params) -> Optional[AbstractStorage[T]]:
    try:
        impl = next((impl.value for impl in StorageImplementation if impl.name.lower() == params.type.lower()))
        return impl(params)
    except StopIteration:
        return None
