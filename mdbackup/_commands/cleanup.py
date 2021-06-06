import logging
from pathlib import Path
import re
import shutil
from typing import List

from ..config import Config
from ..hooks import run_hook
from ..storage import create_storage_instance


def _get_backup_folders_sorted(backups_folder: Path) -> List[Path]:
    """
    Gets the backups folders sorted.
    """
    regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}')
    folders = [folder for folder in backups_folder.iterdir() if folder.is_dir() and regex.match(folder.name)]
    folders.sort()
    return [folder.absolute() for folder in folders]


def _local_cleanup(config: Config):
    logger = logging.getLogger(__name__).getChild('local')
    max_backups = config.max_backups_kept
    if max_backups == 0 or max_backups is None:
        logger.debug('Ignoring local cleanup')
        return

    backups_list = _get_backup_folders_sorted(config.backups_path)
    logger.debug('List of folders available:\n{}'.format('\n'.join([str(b) for b in backups_list])))
    for old in backups_list[0:max(0, len(backups_list) - max_backups)]:
        logger.warning(f'Removing old backup folder {old}')
        run_hook('backup:cleanup:local:pre', {
            'path': str(old.absolute()),
        })
        try:
            shutil.rmtree(str(old.absolute()))
            run_hook('backup:cleanup:local:post', {
                'path': str(old.absolute()),
            })
        except OSError as e:
            logger.exception(f'Could not completely remove backup {old}')
            run_hook('backup:cleanup:local:error', {
                'path': str(old.absolute()),
                'message': str(e),
            })


def _cloud_cleanup(config: Config):
    logger = logging.getLogger(__name__).getChild('cloud')
    regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}')
    for prov_config in config.cloud.providers:
        if prov_config.max_backups_kept is None:
            logger.debug(f'Ignoring entry of type {prov_config.type} because maxBackupsKept is not set')
            continue
        storage = create_storage_instance(prov_config)
        if storage is None:
            continue

        try:
            logger.info(f'Starting cleanup for {prov_config.type} at {prov_config.backups_path}')
            folders = [key for key in storage.list_directory('') if regex.match(str(key))]
            folders.sort()
            logger.debug('List of folders available:\n{}'.format('\n'.join([str(b) for b in folders])))
            for old in folders[0:max(0, len(folders) - prov_config.max_backups_kept)]:
                logger.warning(f'Removing old backup folder {old} of {prov_config.type}')
                run_hook('backup:cleanup:cloud:pre', {
                    'type': prov_config.type,
                    'backupsPath': prov_config.backups_path,
                    'path': str(old),
                })
                storage.delete(old)
                run_hook('backup:cleanup:cloud:post', {
                    'type': prov_config.type,
                    'backupsPath': prov_config.backups_path,
                    'path': str(old),
                })
        except Exception as e:
            logger.exception(e)
            run_hook('backup:cleanup:cloud:error', {
                'type': prov_config.type,
                'backupsPath': prov_config.backups_path,
                'message': str(e),
            })

        del storage


def main_cleanup(config: Config):
    """
    Cleans up backups in local storage and cloud storage.
    """
    # Cleanup old backups in local storage
    _local_cleanup(config)

    # Cleanup old backups in cloud storages
    _cloud_cleanup(config)
