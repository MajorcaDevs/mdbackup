import logging
from pathlib import Path
from typing import Optional

from mdbackup.actions.runner import run_task_actions
from mdbackup.config import CloudConfig


def archive_folder(backup_path: Path, folder: Path, cloud_config: CloudConfig) -> str:
    """
    Given a folder of a backup, archives it into a ``tar`` file and, optionally, compresses the file using different
    strategies. By default, no compression is done.

    A strategy function must be a function that returns a tuple of the command to execute (as pipe) for compress the
    ``tar`` file and the extension to add to the file name. There's some predefined strategies that you can
    use to compress the folder, all available in this package.

    The returned value is the file name for the archived folder.
    """
    logger = logging.getLogger(__name__).getChild('archive_folder')
    filename = str(folder.relative_to(backup_path)) + '.tar'
    actions = [
        {'from-directory': str(folder)},
        {'tar': None},
    ]

    if cloud_config.compression_strategy is not None:
        actions.append({
            f'compress-{cloud_config.compression_strategy}': {
                'level': cloud_config.compression_level,
                'cpus': cloud_config.compression_cpus,
            },
        })
        filename += f'.{cloud_config.compression_strategy}'
    if cloud_config.cypher_strategy is not None:
        actions.append({
            'encrypt-gpg': {
                'passphrase': cloud_config.cypher_params.get('passphrase'),
                'recipients': cloud_config.cypher_params.get('keys', []),
                'algorithm': cloud_config.cypher_params.get('algorithm'),
            },
        })
        filename += '.asc'

    actions.append({'to-file': {'_backup_path': backup_path, 'to': filename}})

    # Do the magic
    logger.info(f'Compressing/encrypting directory {folder} into {filename}')
    run_task_actions('archive-folder', actions)

    return filename


def archive_file(backup_path: Path, file_path: Path, task: dict, cloud_config: CloudConfig) -> Optional[str]:
    logger = logging.getLogger(__name__).getChild('archive_file')

    # Gets the actions used in this file and check if it is compressed or encrypted using any action
    actions = [next(iter(item.keys())) for item in task['actions']]
    has_compress_action = len([item for item in actions if 'compress-' in item]) != 0
    has_encrypt_action = len([item for item in actions if 'encrypt-' in item]) != 0

    filename = str(file_path.relative_to(backup_path))
    archive_actions = [
        {'from-file': str(file_path)},
    ]

    if cloud_config.compression_strategy is not None and not has_compress_action:
        archive_actions.append({
            f'compress-{cloud_config.compression_strategy}': {
                'level': cloud_config.compression_level,
                'cpus': cloud_config.compression_cpus,
            },
        })
        filename += f'.{cloud_config.compression_strategy}'
    if cloud_config.cypher_strategy is not None and not has_encrypt_action:
        archive_actions.append({
            'encrypt-gpg': {
                'passphrase': cloud_config.cypher_params.get('passphrase'),
                'recipients': cloud_config.cypher_params.get('keys', []),
                'algorithm': cloud_config.cypher_params.get('algorithm'),
            },
        })
        filename += '.asc'

    # If no extra actions are required, then just return and do nothing
    if len(archive_actions) == 1:
        logger.info(f'File {file_path} will not compress/encrypt because it is not required')
        return None

    archive_actions.append({'to-file': {'_backup_path': backup_path, 'to': filename}})

    # Do the magic
    logger.info(f'Compressing/encrypting file {file_path} into {filename}')
    run_task_actions('archive-file', archive_actions)

    return filename
