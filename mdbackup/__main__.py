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
from json.decoder import JSONDecodeError
import logging
from pathlib import Path
import re
import shutil
import sys
from typing import Dict, List, Tuple

from .archive import (
    archive_folder,
    get_compression_strategy,
    get_cypher_strategy,
)
from .backup import do_backup, get_backup_folders_sorted
from .config import Config, StorageConfig
from .hooks import define_hook, run_hook
from .secrets import get_secret_backend_implementation
from .storage import create_storage_instance


def main_load_secrets(logger: logging.Logger, config: Config):
    # Prepare secret backends (if any) and its env getters (aka functions that gets the right value from the backend)
    try:
        secret_backends = [(get_secret_backend_implementation(secret.type, secret.config), secret)
                           for secret in config.secrets]
    except ImportError as e:
        # Log not-found module and exit
        logger.exception(e.args[0], e.args[1])
        sys.exit(4)

    try:
        secret_env = {}
        for secret_backend, secret in secret_backends:
            for key, secret_key in secret.env.items():
                logger.debug(f'Getting env secret {key} from {secret.type}:{secret_key}')
                secret_env[key] = secret_backend.get_secret(secret_key)

        for secret_backend, secret in secret_backends:
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
                config.providers.append(provider)
    except Exception as e:
        raise e
    finally:
        for secret_backend, _ in secret_backends:
            del secret_backend

    return secret_env


def main_do_backup(logger: logging.Logger, config: Config, secret_env) -> Path:
    # Do backups
    try:
        cypher_items = config.cypher_params.items() if config.cypher_params is not None else []
        cypher_env = {f'cypher_{key}': value for key, value in cypher_items}
        return do_backup(config.backups_path,
                         config.config_folder,
                         config.custom_utils_script,
                         **config.env,
                         compression_strategy=config.compression_strategy,
                         compression_level=config.compression_level,
                         cypher_strategy=config.cypher_strategy,
                         **cypher_env,
                         **secret_env)
    except Exception as e:
        logger.error(e)
        run_hook('backup:error', str(config.backups_path / '.partial'), str(e), e.args[1] if len(e.args) > 2 else '')
        shutil.rmtree(str(config.backups_path / '.partial'))
        sys.exit(1)


def main_compress_folders(config: Config, backup: Path) -> Tuple[List[Path], List[Path]]:
    final_items = []
    items_to_remove = []

    # Compress directories
    for item in backup.iterdir():
        # Compress if it is a directory
        if item.resolve().is_dir():
            strategies = []

            if config.compression_strategy is not None:
                strategies.append(get_compression_strategy(
                    config.compression_strategy,
                    config.compression_level,
                ))

            if config.cypher_strategy is not None:
                strategies.append(get_cypher_strategy(
                    config.cypher_strategy,
                    **config.cypher_params,
                ))

            filename = archive_folder(backup, item.resolve(), strategies)

            final_items.append(Path(backup, filename))
            items_to_remove.append(Path(backup, filename))
        else:
            final_items.append(item.resolve())

    return final_items, items_to_remove


def main_upload_backup(logger: logging.Logger, config: Config, backup: Path):
    has_compressed = False
    final_items, items_to_remove = None, []

    # (do the following only if there are any providers defined)
    if len(config.providers) == 0:
        return

    try:
        # Upload files to storage providers
        backup_folder_name = backup.relative_to(config.backups_path.resolve()).parts[0]
        for prov_config in config.providers:
            # Detect provider type and instantiate it
            storage = create_storage_instance(prov_config)

            if storage is not None:
                if not has_compressed:
                    final_items, items_to_remove = main_compress_folders(config, backup)
                    has_compressed = True

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
                for item in final_items:
                    try:
                        logger.info(f'Uploading {item} to {backup_cloud_folder}')
                        storage.upload(item, backup_cloud_folder)
                    except Exception as e:
                        # Log only in case of error (tries to upload as much as it can)
                        run_hook('upload:error', prov_config.type, str(backup), str(e))
                        logger.exception(f'Could not upload file {item}: {e}')

                run_hook('upload:after', prov_config.type, str(backup), str(backup_cloud_folder))
                del storage
            else:
                # The provider is invalid, show error
                logger.error(f'Unknown storage provider "{prov_config.type}", ignoring...')
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
    for prov_config in config.providers:
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
        if s.type == 'file' and s.config.get('basePath') is None:
            s.config['basePath'] = str(config.config_folder / 'secrets')


def main():
    parser = argparse.ArgumentParser(description=('Small but customizable utility to create backups and store them in '
                                                  'cloud storage providers'))

    parser.add_argument('-c', '--config',
                        help='Path to configuration folder (default: config)',
                        default='config')
    parser.add_argument('--backup-only',
                        help='Only does the backup actions',
                        action='store_true',
                        default=False)
    parser.add_argument('--upload-current-only',
                        help='Only uploads the last backup',
                        action='store_true',
                        default=False)
    parser.add_argument('--cleanup-only',
                        help='Only does the backup cleanup',
                        action='store_true',
                        default=False)

    args = parser.parse_args()

    # Check if configuration file exists and read it
    try:
        config = Config(args.config)
    except (FileNotFoundError, NotADirectoryError, NotImplementedError) as e:
        print(e.args[0])
        print('Check the paths and run again the utility')
        sys.exit(1)
    except KeyError as e:
        print('Configuration is malformed')
        print(e.args[0])
        sys.exit(2)
    except JSONDecodeError as e:
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
        if args.backup_only:
            secret_env = main_load_secrets(logger, config)
            backup = main_do_backup(logger, config, secret_env)
            logger.info(f'Backup done: {backup.absolute()}')
        elif args.upload_current_only:
            main_load_secrets(logger, config)
            main_upload_backup(logger, config, (config.backups_path / 'current').resolve())
        elif args.cleanup_only:
            main_clean_up(logger, config)
        else:
            secret_env = main_load_secrets(logger, config)
            backup = main_do_backup(logger, config, secret_env)
            main_upload_backup(logger, config, backup)
            main_clean_up(logger, config)
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
