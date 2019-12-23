from abc import ABC, abstractmethod
from typing import Dict


class AbstractSecretsBackend(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> str:
        pass

    @abstractmethod
    def get_provider(self, key: str) -> Dict[str, any]:
        pass

    def __del__(self):
        pass
