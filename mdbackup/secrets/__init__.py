from typing import Dict

from mdbackup.secrets.file_backend import FileSecretsBackend
from mdbackup.secrets.secrets import AbstractSecretsBackend
from mdbackup.secrets.vault_backend import VaultSecretsBackend


def get_secret_backend_implementation(name: str, config: Dict[str, any]) -> AbstractSecretsBackend:
    return {
        'file': FileSecretsBackend,
        'vault': VaultSecretsBackend,
    }[name](config)
