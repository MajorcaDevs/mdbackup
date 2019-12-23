from io import StringIO
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from mdbackup.config import Config
import mdbackup.jsonschemavalidator


class ConfigTests(TestCase):
    _supported_types = ['json', 'yaml']
    _valid_config_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'valid',
    )
    _invalid_config_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'invalid',
    )
    _wrong_config_path = Path(os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        'wrong',
    ))

    _test_config = Config({
        'actionsModules': [
            '1#f',
            '2#g',
        ],
        'backupsPath': '/',
        'maxBackupsKept': -1,
        'logLevel': 'INFO',
        'env': {
            'a.d.2': 'ñ',
        },
        'hooks': {
            'backup:before': 'ou yeah',
        },
        'secrets': {
            'file': {
                'envDefs': {
                    'ou': 'yeah',
                },
                'config': {
                    'basePath': '/there',
                },
                'storageProviders': [
                    'provider-1',
                    {'key': 'provider-2', 'extra': 1},
                ],
            },
        },
        'cloud': {
            'compression': {
                'method': 'xz',
                'level': 8,
            },
            'encrypt': {
                'strategy': 'gpg-keys',
                'keys': [
                    'me@you.org',
                ],
                'passphrase': '1234',
                'algorithm': 'AES256',
            },
            'providers': [
                {'type': 'gdrive', 'backupsPath': '/backups'},
            ],
        },
    })

    def __init__(self, *args):
        super().__init__(*args)
        self._valid_config = {_type: os.path.join(self._valid_config_path, _type) for _type in self._supported_types}
        self._invalid_config = {_type: os.path.join(self._invalid_config_path, _type)
                                for _type in self._supported_types}
        self._wrong_config = {_type: os.path.join(self._wrong_config_path, _type) for _type in self._supported_types}

    def test_parse_valid_config_should_work(self):
        for key, path in self._valid_config.items():
            with self.subTest(key):
                Config(path)

    def test_parse_valid_config_should_have_the_same_values(self):
        for key, path in self._valid_config.items():
            with self.subTest(key):
                config = Config(path)

                with self.subTest(f'{key} - actionsModules'):
                    self.assertListEqual(self._test_config.actions_modules, config.actions_modules)
                with self.subTest(f'{key} - backupsPath'):
                    self.assertEqual(self._test_config.backups_path, config.backups_path)
                with self.subTest(f'{key} - maxBackupsKept'):
                    self.assertEqual(self._test_config.max_backups_kept, config.max_backups_kept)
                with self.subTest(f'{key} - logLevel'):
                    self.assertEqual(self._test_config.log_level, config.log_level)
                with self.subTest(f'{key} - env'):
                    self.assertDictEqual(self._test_config.env, config.env)
                with self.subTest(f'{key} - hooks'):
                    self.assertEqual(self._test_config.hooks, config.hooks)
                with self.subTest(f'{key} - secrets'):
                    self.assertIsNotNone(config.secrets)
                    self.assertEqual(len(self._test_config.secrets), len(config.secrets))
                    for i in range(0, len(self._test_config.secrets)):
                        parsed_secret = config.secrets[i]
                        test_secret = self._test_config.secrets[i]
                        self.assertEqual(test_secret.type, parsed_secret.type)
                        self.assertDictEqual(test_secret.env, parsed_secret.env)
                        self.assertListEqual(test_secret.storage, parsed_secret.storage)
                        self.assertIsNotNone(parsed_secret.backend)
                with self.subTest(f'{key} - cloud'):
                    self.assertIsNotNone(config.cloud)
                    self.assertEqual(self._test_config.cloud.compression_strategy, config.cloud.compression_strategy)
                    self.assertEqual(self._test_config.cloud.compression_level, config.cloud.compression_level)
                    self.assertEqual(self._test_config.cloud.cypher_strategy, config.cloud.cypher_strategy)
                    self.assertDictEqual(self._test_config.cloud.cypher_params, config.cloud.cypher_params)
                    self.assertEqual(len(self._test_config.cloud.providers), len(config.cloud.providers))
                    for i in range(0, len(self._test_config.cloud.providers)):
                        parsed_provider = config.cloud.providers[i]
                        test_provider = self._test_config.cloud.providers[i]
                        self.assertEqual(test_provider.type, parsed_provider.type)
                        self.assertEqual(test_provider.backups_path, parsed_provider.backups_path)
                        self.assertEqual(test_provider.max_backups_kept, parsed_provider.max_backups_kept)
                        self.assertDictEqual(test_provider._StorageConfig__extra, parsed_provider._StorageConfig__extra)

    def test_non_existing_path_should_raise_filenotfounderror(self):
        with self.assertRaisesRegex(FileNotFoundError, 'must exist$'):
            Config('f')

    def test_existing_path_not_being_a_directory_should_raise_notadirectoryerror(self):
        with self.assertRaisesRegex(NotADirectoryError, 'must be a directory$'):
            Config(Path(self._valid_config_path) / 'json' / 'config.json')

    def test_with_existing_folder_but_with_no_config_should_raise_filenotfounderror(self):
        with self.assertRaisesRegex(FileNotFoundError, 'config.json, config.yaml or config.yml'):
            Config(Path(self._valid_config_path).parent)

    @patch('mdbackup.config.configuration.validate')
    def test_invalid_config_should_raise(self, validate):
        validate.side_effect = lambda schema, data: mdbackup.jsonschemavalidator.validate(schema, data, StringIO())
        for key, path in self._wrong_config.items():
            with self.subTest(key):
                with self.assertRaisesRegex(Exception, '^Configuration is invalid$'):
                    Config(path)

    def test_parse_errors_should_raise(self):
        for key, path in self._invalid_config.items():
            with self.subTest(key):
                with self.assertRaises(Exception):
                    Config(path)
