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

import json
import logging
from pathlib import Path
import shutil
import subprocess
import sys

from .archive import (
    archive_folder,
    get_compression_strategy,
    gpg_passphrase_strategy,
    gpg_key_strategy,
    gzip_strategy,
)
from .backup import do_backup, get_backup_folders_sorted
from .config import Config
from .storage.storage import create_storage_instance

def main():
    #Check if configuration file exists and read it
    try:
        config = Config('config/config.json')
    except (FileNotFoundError, IsADirectoryError, NotADirectoryError) as e:
        print(e.args[0])
        print('Check the paths and run again the utility')
        sys.exit(1)
    except KeyError as e:
        print('Configuration is malformed')
        print(e.args[0])
        sys.exit(2)

    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        level=config.log_level)
    logger = logging.getLogger('mdbackups')

    #Do backups
    backups_path = config.backups_path
    backup = do_backup(backups_path,
                       config.custom_utils_script,
                       **config.env,
                       compression_strategy=config.compression_strategy,
                       compression_level=config.compression_level)
    final_items = []
    items_to_remove = []

    #(do the following only if there are any providers defined)
    if len(config.providers) > 0:
        #Compress directories
        for item in backup.iterdir():
            #Compress if it is a directory
            if item.is_dir():
                strategies = []

                if config.compression_strategy is not None:
                    strategies.append(get_compression_strategy(
                        config.compression_strategy,
                        config.compression_level,
                    ))

                if 'gpg_key' in config.env:
                    strategies.append(gpg_key_strategy(config.env['gpg_keys']))
                elif 'gpg_passphrase' in config.env:
                    strategies.append(gpg_passphrase_strategy(config.env['gpg_passphrase']))

                filename = archive_folder(backup, item, strategies)

                final_items.append(Path(backup, filename))
                items_to_remove.append(Path(backup, filename))
            else:
                final_items.append(item)

        try:
            #Upload files to storage providers
            backup_folder_name = backup.relative_to(backups_path).parts[0]
            for prov_config in config.providers:
                #Detect provider type and instantiate it
                storage = create_storage_instance(prov_config)

                if storage is not None:
                    #Create folder for this backup
                    try:
                        backup_cloud_folder = storage.create_folder(backup_folder_name, prov_config.backups_path)
                    except Exception:
                        #If we cannot create it, will continue to the next configured provider
                        logger.exception(f'Could not create folder {backup_folder_name}')
                        continue

                    #Upload every file
                    for item in final_items:
                        try:
                            logger.info(f'Uploading {item} to {backup_cloud_folder}')
                            storage.upload(item, backup_cloud_folder)
                        except Exception:
                            #Log only in case of error (tries to upload as much as it can)
                            logger.exception(f'Could not upload file {item}')
                else:
                    #The provider is invalid, show error
                    logger.error(f'Unknown storage provider "{prov_config.type}", ignoring...')
        finally:
            #Remove compressed directories
            for item in items_to_remove:
                logger.info(f'Removing file from compressed directory {item}')
                item.unlink()

    #Cleanup old backups
    max_backups = config.max_backups_kept
    backups_list = get_backup_folders_sorted(backups_path)
    logger.debug('List of folders available:\n{}'.format('\n'.join([str(b) for b in backups_list])))
    for old in backups_list[0:max(0, len(backups_list)-max_backups)]:
        logger.warn(f'Removing old backup folder {old}')
        try:
            shutil.rmtree(old)
        except Exception:
            logger.exception(f'Could not completely remove backup {old}')


if __name__ == '__main__':
    main()
