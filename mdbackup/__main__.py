# Small but customizable utility to create backups and store them in
# cloud storage providers
# Copyright (C) 2018  Melchor Alejo Garau Madrigal
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import argparse
from functools import reduce
from json.decoder import JSONDecodeError
import logging
from pathlib import Path
import re
import shutil
import sys
from typing import Dict, List, Tuple

from yaml.parser import ParserError

from .actions.builtin._register import register
from .actions.container import register_actions_from_module
from .archive import archive_folder
from .backup import do_backup, get_backup_folders_sorted
from .config import Config, StorageConfig
from .hooks import define_hook, run_hook
from .storage import create_storage_instance
from .utils import read_data_file, write_data_file


def main_load_secrets(logger: logging.Logger, config: Config):
    try:
        for secret in config.secrets:
            secret_backend = secret.backend
            for key in secret.storage:
                logger.debug(f'Getting storage provider secret from {secret.type}:{key}')
                if isinstance(key, dict):
                    value = secret_backend.get_provider(key['key'])
                    for o_key, o_value in key.items():
                        value[o_key] = o_value
                else:
                    value = secret_backend.get_provider(key)
                provider = StorageConfig(value)
                logger.debug(f'Provider type is {provider.type}')
                config.cloud.providers.append(provider)
    except Exception as e:
        raise e

    return {}


def main_register_actions(logger: logging.Logger, config: Config):
    # Register builtin actions
    register()
    # Register external actions
    for module in config.actions_modules:
        try:
            register_actions_from_module(module)
        except ValueError as e:
            raise Exception(f'{module}: {" ".join(e.args)}')


def main_do_backup(logger: logging.Logger, config: Config, secret_env) -> Path:
    # Do backups
    try:
        return do_backup(config.backups_path,
                         config.config_folder,
                         config.actions_modules,
                         env={
                            **config.env,
                            **secret_env,
                         },
                         secrets=config.secrets)
    except Exception as e:
        logger.error(e)
        run_hook('backup:error', str(config.backups_path / '.partial'), str(e), e.args[1] if len(e.args) > 2 else '')
        shutil.rmtree(str(config.backups_path / '.partial'))
        sys.exit(1)


def _compress_folders(config: Config, backup: Path, items: List[Path]) -> Tuple[List[Path], List[Path]]:
    final_items = []
    items_to_remove = []

    # Compress directories
    for item in items:
        # Compress if it is a directory
        if item.is_dir():
            filename = archive_folder(backup, item, config.cloud)
            final_items.append(backup / filename)
            items_to_remove.append(backup / filename)
        else:
            final_items.append(item)

    return final_items, items_to_remove


def _upload_backup(config: Config, backup: Path, items: List[Path]) -> bool:
    logger = logging.getLogger('mdbackup').getChild('upload')
    could_upload = False

    # Upload files to storage providers
    backup_folder_name = backup.relative_to(config.backups_path.resolve()).parts[0]
    for prov_config in config.cloud.providers:
        # Detect provider type and instantiate it
        storage = create_storage_instance(prov_config)

        run_hook('upload:before', prov_config.type, str(backup))

        # Create folder for this backup
        try:
            logger.info(f'Creating folder {backup_folder_name} in {prov_config.backups_path}')
            backup_cloud_folder = storage.create_folder(backup_folder_name)
        except Exception as e:
            # If we cannot create it, will continue to the next configured provider
            run_hook('upload:error', prov_config.type, str(backup), str(e))
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
            run_hook('upload:error', prov_config.type, str(backup), str(e))
            logger.exception(f'Could not upload file {item}: {e}')
            storage.delete(backup_cloud_folder)

        run_hook('upload:after', prov_config.type, str(backup), str(backup_cloud_folder))
        del storage

    return could_upload


def main_upload_backup(config: Config, backup: Path, force: bool = False):
    logger = logging.getLogger('mdbackup').getChild('upload')
    final_items, items_to_remove = None, []

    # (do the following only if there are any providers defined)
    if len(config.cloud.providers) == 0:
        logger.warn('No configured cloud storage providers, not uploading anything...')
        return

    if not backup.exists():
        raise FileNotFoundError(backup)
    if not backup.is_dir():
        raise NotADirectoryError(backup)
    if not str(backup).startswith(str(config.backups_path)):
        raise ValueError(f'Backup path {backup} is not inside the backups path')
    manifest = read_data_file(backup / '.manifest.yaml')
    if not force and manifest.get('uploaded', False):
        logger.warn(f'Backup {backup} has been already uploaded')
        return

    try:
        # Get files and folders to upload from the manifest
        tasks = reduce(lambda x, y: [*x, *y],
                       (tasks['tasks'] for tasks in manifest['tasksDefinitions'].values()),
                       [])
        items = (backup / task['result'] for task in tasks)
        items = map(lambda p: p.resolve(), items)

        final_items, items_to_remove = _compress_folders(config, backup, items)
        manifest['uploaded'] = _upload_backup(config, backup, final_items)

        write_data_file(backup / '.manifest.yaml', manifest)
    finally:
        # Remove compressed directories
        for item in items_to_remove:
            logger.info(f'Removing file from compressed directory {item}')
            item.unlink()


def main_clean_up(logger: logging.Logger, config: Config):
    # Cleanup old backups
    max_backups = config.max_backups_kept
    if max_backups == 0 or max_backups is None:
        logger.debug('Ignoring local cleanup')
        return

    backups_list = get_backup_folders_sorted(config.backups_path)
    logger.debug('List of folders available:\n{}'.format('\n'.join([str(b) for b in backups_list])))
    for old in backups_list[0:max(0, len(backups_list) - max_backups)]:
        logger.warning(f'Removing old backup folder {old}')
        run_hook('oldBackup:deleting', str(old.absolute()))
        try:
            shutil.rmtree(str(old.absolute()))
            run_hook('oldBackup:deleted', str(old.absolute()))
        except OSError as e:
            logger.exception(f'Could not completely remove backup {old}')
            run_hook('oldBackup:error', str(old.absolute()), str(e))

    regex = re.compile(r'\d{4}-\d{2}-\d{2}T\d{1,2}:\d{2}')
    for prov_config in config.cloud.providers:
        storage = create_storage_instance(prov_config)
        if storage is None or prov_config.max_backups_kept is None:
            continue

        try:
            logger.info(f'Starting cleanup for {prov_config.type} at {prov_config.backups_path}')
            folders = [key for key in storage.list_directory('') if regex.match(str(key))]
            folders.sort()
            for old in folders[0:max(0, len(folders) - prov_config.max_backups_kept)]:
                logger.warning(f'Removing old backup folder {old} of {prov_config.type}')
                run_hook('oldBackup:storage:deleting', prov_config.type, prov_config.backups_path, str(old))
                storage.delete(old)
                run_hook('oldBackup:storage:deleted', prov_config.type, prov_config.backups_path, str(old))
        except Exception as e:
            logger.exception(e)
            run_hook('oldBackup:storage:error', prov_config.type, prov_config.backups_path, str(e))


def configure_hooks(hooks: Dict[str, str]):
    [define_hook(name, script) for (name, script) in hooks.items()]


def configure_default_value_for_file_secrets(config: Config):
    for s in config.secrets:
        if s.type == 'file':
            if s.config.get('basePath') is None:
                s.config['basePath'] = str(config.config_folder / 'secrets')
            elif not Path(s.config['basePath']).is_absolute():
                s.config['basePath'] = str(config.config_folder / s.config['basePath'])


def parse_arguments():
    parser = argparse.ArgumentParser(description=('Small but customizable utility to create backups and store them in '
                                                  'cloud storage providers'))

    parser.add_argument('-c', '--config',
                        help='Path to configuration folder (default: config)',
                        default='config')
    subparsers = parser.add_subparsers(description='Selects the run mode (defaults to complete)',
                                       metavar='mode',
                                       dest='mode')

    subparsers.add_parser('complete',
                          help='Checks config, does a backup, uploads the backup and does cleanup')
    subparsers.add_parser('backup', help='Does a backup')
    upload_parser = subparsers.add_parser('upload', help='Upload a pending backups')
    subparsers.add_parser('cleanup', help='Does cleanup of backups')
    subparsers.add_parser('check-config', help='Checks configuration to catch issues')

    upload_parser.add_argument('--backup',
                               help=('Selects which backup to upload by the name of the folder (which is the date of '
                                     'the backup)'))
    upload_parser.add_argument('-f', '--force',
                               help='Force upload the backup even if the backup was already uploaded',
                               action='store_true')

    return parser.parse_args()


def main():
    args = parse_arguments()

    # Check if configuration file exists and read it
    try:
        config = Config(args.config)
    except (FileNotFoundError, NotADirectoryError, NotImplementedError) as e:
        print(' '.join(e.args))
        print('Check the paths and run again the utility')
        sys.exit(1)
    except KeyError as e:
        print('Configuration is malformed')
        print(e.args[0])
        sys.exit(2)
    except (JSONDecodeError, ParserError) as e:
        print('Configuration is malformed')
        print(e.args[0])
        sys.exit(3)

    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        level=config.log_level)
    logger = logging.getLogger('mdbackup')

    # Configure hooks
    configure_hooks(config.hooks)

    # Set default paths for file secret backends (I don't like this)
    configure_default_value_for_file_secrets(config)

    try:
        main_register_actions(logger, config)
        if args.mode == 'backup':
            secret_env = main_load_secrets(logger, config)
            backup = main_do_backup(logger, config, secret_env)
            logger.info(f'Backup done: {backup.absolute()}')
        elif args.mode == 'upload':
            if args.backup is not None:
                backup_path = config.backups_path / args.backup
            else:
                backup_path = (config.backups_path / 'current').resolve()
            main_load_secrets(logger, config)
            main_upload_backup(config, backup_path, force=args.force)
        elif args.mode == 'cleanup':
            main_clean_up(logger, config)
        elif not args.validate_config:
            secret_env = main_load_secrets(logger, config)
            backup = main_do_backup(logger, config, secret_env)
            main_upload_backup(config, backup)
            main_clean_up(logger, config)
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
