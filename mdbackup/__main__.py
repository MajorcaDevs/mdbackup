import argparse
from json.decoder import JSONDecodeError
import logging
from pathlib import Path
import sys
from typing import Dict

from yaml.parser import ParserError

from ._commands.backup import main_backup
from ._commands.cleanup import main_cleanup
from ._commands.upload import main_upload
from .actions.builtin._register import register
from .actions.container import register_actions_from_module
from .config import Config, StorageConfig
from .hooks import define_hook


def _load_secrets(config: Config):
    logger = logging.getLogger('mdbackup').getChild('load_secrets')
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


def _register_actions(config: Config):
    # Register builtin actions
    register()
    # Register external actions
    for module in config.actions_modules:
        try:
            register_actions_from_module(module)
        except ValueError as e:
            raise Exception(f'{module}: {" ".join(e.args)}')


def _configure_hooks(hooks: Dict[str, str]):
    [define_hook(name, script) for (name, script) in hooks.items()]


def _configure_default_value_for_file_secrets(config: Config):
    for s in config.secrets:
        if s.type == 'file':
            if s.config.get('basePath') is None:
                s.config['basePath'] = str(config.config_folder / 'secrets')
            elif not Path(s.config['basePath']).is_absolute():
                s.config['basePath'] = str(config.config_folder / s.config['basePath'])


def _parse_arguments():
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


def _read_config(path: str) -> Config:
    try:
        return Config(path)
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


def main():
    args = _parse_arguments()

    # Check if configuration file exists and read it
    config = _read_config(args.config)

    # Configure logging
    logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                        level=config.log_level)
    logger = logging.getLogger('mdbackup')

    # Configure hooks
    _configure_hooks(config.hooks)

    # Set default paths for file secret backends (I don't like this)
    _configure_default_value_for_file_secrets(config)

    # Register builtin actions and external actions
    _register_actions(config)

    try:
        _load_secrets(config)
        if args.mode == 'backup':
            backup = main_backup(config)
            logger.info(f'Backup done: {backup.absolute()}')
        elif args.mode == 'upload':
            backup_path = (config.backups_path / (args.backup if args.backup is not None else 'current')).resolve()
            main_upload(config, backup_path, force=args.force)
        elif args.mode == 'cleanup':
            main_cleanup(config)
        elif args.mode in ('complete', None):
            backup = main_backup(config)
            main_upload(config, backup)
            main_cleanup(config)
    except Exception as e:
        logger.exception(e)


if __name__ == '__main__':
    main()
