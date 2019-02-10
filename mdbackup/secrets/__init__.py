from typing import Dict

from mdbackup.check_packages import check, check_requests
from mdbackup.secrets.secrets import AbstractSecretsBackend


@check('file secrets backend')
def load_file_secrets_backend():
    from mdbackup.secrets.file_backend import FileSecretsBackend
    return FileSecretsBackend


@check('Vault secrets backend', check_requests)
def load_vault_secrets_backend():
    from mdbackup.secrets.vault_backend import VaultSecretsBackend
    return VaultSecretsBackend


def get_secret_backend_implementation(name: str, config: Dict[str, any]) -> AbstractSecretsBackend:
    try:
        return {
            'file': load_file_secrets_backend,
            'vault': load_vault_secrets_backend,
        }[name]()(config)
    except KeyError as e:
        raise KeyError(f'Could not found secret backend {e.args[0]}', e)
