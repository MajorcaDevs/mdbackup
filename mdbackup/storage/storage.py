from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Union


class AbstractStorage(ABC):
    @abstractmethod
    def list_directory(self, path: Union[str, Path]) -> List[str]:
        pass

    @abstractmethod
    def create_folder(self, name: str, parent: Union[Path, str] = None) -> str:
        pass

    @abstractmethod
    def upload(self, path: Path, parent: Union[Path, str, Path] = None):
        pass

    @abstractmethod
    def delete(self, path: Union[Path, str]):
        pass
