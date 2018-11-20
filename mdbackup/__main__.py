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

from .backup import do_backup, get_backup_folders_sorted
from .storage.drive import GDriveStorage

def main():
    #Check if configuration file exists
    if not Path('config/config.json').exists():
        print('Config file "' + str(Path('config/config.json').absolute()) + '" does not exist')
        print('Check the paths and run again the utility')
        sys.exit(1)

    #Read the configuration
    with open('config/config.json') as config_file:
        config = json.load(config_file)

    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        level=logging.getLevelName(config.get('logLevel', 'WARNING')))
    logger = logging.getLogger('mdbackups')

    #Do backups
    backups_path = Path(config['backupsPath'])
    backup = do_backup(backups_path, config.get('customUtilsScript'), **config['env'])
    final_items = []
    items_to_remove = []

    #(do the following only if there are any providers defined)
    if len(config['providers']) > 0:
        #Compress directories
        for item in backup.iterdir():
            #Compress if it is a directory
            if item.is_dir():
                filename = item.parts[-1] + '.tar'
                directory = item.relative_to(backup)
                logger.info(f'Compressing directory {item} into {filename}')
                #If a GPG passphrase is defined, compress and cypher using GPG
                if 'gpg_passphrase' in config['env']:
                    filename += '.gpg'
                    end_cmd = f'| gpg --output "{filename}" --batch --passphrase "{config["env"]["gpg_passphrase"]}" --symmetric -'
                else:
                    filename += '.gz'
                    end_cmd = f'| gzip > "{filename}"'

                #Do the compression
                logger.debug(f'Executing command ["bash", "-c", \'tar -c "{str(directory)}" {end_cmd}\']')
                _exec = subprocess.run(['bash', '-c', f'tar -c "{str(directory)}" {end_cmd}'],
                                    cwd=str(backup), check=True)
                final_items.append(Path(backup, filename))
                items_to_remove.append(Path(backup, filename))
            else:
                final_items.append(item)

        try:
            #Upload files to storage providers
            backup_folder_name = backup.relative_to(backups_path).parts[0]
            for prov_config in config['providers']:
                gd = None
                #Detect provider type and instantiate it
                if 'gdrive' == prov_config['type']:
                    logger.info('Preparing upload to Google Drive')
                    gd = GDriveStorage(prov_config.get('clientSecrets'), prov_config.get('authTokens'))

                if gd is not None:
                    #Create folder for this backup
                    try:
                        backup_cloud_folder = gd.create_folder(backup_folder_name, prov_config['backupsPath'])
                    except Exception:
                        #If we cannot create it, will continue to the next configured provider
                        logger.exception(f'Could not create folder {backup_folder_name}')
                        continue

                    #Upload every file
                    for item in final_items:
                        try:
                            logger.info(f'Uploading {item} to {backup_cloud_folder}')
                            gd.upload(item, backup_cloud_folder)
                        except Exception:
                            #Log only in case of error (tries to upload as much as it can)
                            logger.exception(f'Could not upload file {item}')
                else:
                    #The provider is invalid, show error
                    logger.error(f'Unknown storage provider "{prov_config["type"]}", ignoring...')
        finally:
            #Remove compressed directories
            for item in items_to_remove:
                logger.info(f'Removing file from compressed directory {item}')
                item.unlink()

    #Cleanup old backups
    max_backups = config.get('maxBackupsKept', 7)
    backups_list = get_backup_folders_sorted(backups_path)
    logger.debug('List of folders available:\n{}'.format('\n'.join(backups_list)))
    for old in backups_list[0:(len(backups_list)-max_backups)]:
        logger.warn(f'Removing old backup folder {old}')
        try:
            shutil.rmtree(old)
        except Exception:
            logger.exception(f'Could not remove completely {old}')


if __name__ == '__main__':
    main()
