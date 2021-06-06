from functools import reduce
import logging
from pathlib import Path
from typing import Iterable, List, Tuple

from ..archive import archive_file, archive_folder
from ..config import Config
from ..hooks import run_hook
from ..storage import create_storage_instance
from ..utils import read_data_file, write_data_file


def _process_results(config: Config, backup: Path, items: Iterable[Tuple[Path, dict]]) -> Tuple[List[Path], List[Path]]:
    """
    Given a backup folder and the items from the backup manifest, process all items in order to be uploaded and returns
    a list of all items to upload and a list of items to be removed.

    Right now, the only processed items are directories whose contents are archived in a tar file and based on the
    cloud configuration, compressed and/or encrypted. Those new files are stored in the manifest to be easily identified
    when a restore is being done.
    """
    final_items = []
    items_to_remove = []

    # Compress directories
    for item, task in items:
        if item.is_dir():
            # Compress/encrypt if it is a directory
            filename = archive_folder(backup, item, config.cloud)
            final_items.append(backup / filename)
            items_to_remove.append(backup / filename)
            task['cloudResult'] = Path(filename)
        else:
            # Compress/encrypt if it is a file (if needed)
            filename = archive_file(backup, item, task, config.cloud)
            if filename is not None:
                final_items.append(backup / filename)
                items_to_remove.append(backup / filename)
                task['cloudResult'] = Path(filename)
            else:
                final_items.append(item)

    # Add the manifest as well :)
    manifest_filename = archive_file(backup, backup / '.manifest.yaml', {'actions': []}, config.cloud)
    if manifest_filename is not None:
        final_items.append(backup / manifest_filename)
        items_to_remove.append(backup / manifest_filename)
    else:
        final_items.append(backup / '.manifest.yaml')
    return final_items, items_to_remove


def _upload_backup(config: Config, backup: Path, items: Iterable[Path]) -> bool:
    """
    Uploads backup to all cloud storage providers
    """
    logger = logging.getLogger('mdbackup').getChild('upload')
    could_upload = False

    # Upload files to storage providers
    backup_folder_name = backup.relative_to(config.backups_path.resolve()).parts[0]
    for prov_config in config.cloud.providers:
        # Detect provider type and instantiate it
        storage = create_storage_instance(prov_config)

        run_hook('upload:pre', {
            'type': prov_config.type,
            'localPath': str(backup),
            'remoteBackupsPath': prov_config.backups_path,
            'files': list(items),
        })

        # Create folder for this backup
        try:
            logger.info(f'Creating folder {backup_folder_name} in {prov_config.backups_path}')
            backup_cloud_folder = storage.create_folder(backup_folder_name)
        except Exception as e:
            # If we cannot create it, will continue to the next configured provider
            run_hook('upload:error', {
                'type': prov_config.type,
                'localPath': str(backup),
                'remoteBackupsPath': prov_config.backups_path,
                'message': str(e),
            })
            logger.exception(f'Could not create folder {backup_folder_name}', e)
            continue

        # Upload every file
        try:
            for item in items:
                parent = item.relative_to(backup).parent
                cloud_folder = backup_cloud_folder
                if parent != Path('.'):
                    logger.info(f'Creating parent folder {parent} for {item}')
                    for part in parent.parts:
                        cloud_folder = storage.create_folder(part, cloud_folder)
                logger.info(f'Uploading {item} to {cloud_folder}')
                storage.upload(item, cloud_folder)

            could_upload = True
        except Exception as e:
            # Log only in case of error
            run_hook('upload:error', {
                'type': prov_config.type,
                'localPath': str(backup),
                'remoteBackupsPath': prov_config.backups_path,
                'remotePath': backup_cloud_folder,
                'item': str(item),
                'message': str(e),
            })
            logger.exception(f'Could not upload file {item}: {e}')
            storage.delete(backup_cloud_folder)

        run_hook('upload:post', {
            'type': prov_config.type,
            'localPath': str(backup),
            'remoteBackupsPath': prov_config.backups_path,
            'remotePath': backup_cloud_folder,
        })
        del storage

    return could_upload


def _get_generated_files_from_manifest(manifest: dict, backup: Path) -> Iterable[Tuple[Path, dict]]:
    """
    From a parsed backup manifest, gets all results from tasks.
    """
    tasks = reduce(lambda x, y: [*x, *y],
                   (tasks['tasks'] for tasks in manifest['tasksDefinitions'].values()),
                   [])
    # only get results if can be uploaded and are not None (aka failed)
    items = ((backup / task['result'], task) for task in tasks
             if not task['cloud'].ignore and task.get('result') is not None)
    items = map(lambda p: (p[0].resolve(), p[1]), items)
    return items


def main_upload(config: Config, backup: Path, force: bool = False):
    """
    Prepares the items of the backup to be uploaded and uploads them on each cloud storage provider.

    The function will check if the path is really a backup, then it will prepare the backup to be uploaded,
    update the manifest with the transformed items and upload all files into each cloud storage provider.
    """
    logger = logging.getLogger('mdbackup').getChild('upload')
    final_items, items_to_remove = None, []

    # (do the following only if there are any providers defined)
    if len(config.cloud.providers) == 0:
        logger.warning('No configured cloud storage providers, not uploading anything...')
        return

    if not backup.exists():
        raise FileNotFoundError(backup)
    if not backup.is_dir():
        raise NotADirectoryError(backup)
    if not str(backup).startswith(str(config.backups_path.resolve())):
        raise ValueError(f'Backup path {backup} is not inside the backups path')
    manifest_path = backup / '.manifest.yaml'
    if not manifest_path.exists():
        raise FileNotFoundError(f'Backup manifest does not exist in the folder {backup}')
    manifest = read_data_file(manifest_path)
    if not force and manifest.get('uploaded', False):
        logger.warning(f'Backup {backup} has been already uploaded')
        return

    try:
        # Get files and folders to upload from the manifest (with their respective tasks)
        items = _get_generated_files_from_manifest(manifest, backup)
        # Archive folders (using tar) and compress and/or encrypt if configured and store in manifest paths for the
        # archived folders so it will be easier to retrieve them in restores
        final_items, items_to_remove = _process_results(config, backup, items)
        write_data_file(manifest_path, manifest)
        # Upload files
        manifest['uploaded'] = _upload_backup(config, backup, final_items)
        # Write to manifest if upload was successful
        write_data_file(manifest_path, manifest)
    finally:
        # Remove compressed directories
        for item in items_to_remove:
            logger.info(f'Removing temporary file {item}')
            item.unlink()
