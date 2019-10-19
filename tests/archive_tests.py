from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from mdbackup.actions.builtin._register import register
from mdbackup.actions.container import _clean_actions
from mdbackup.archive import archive_folder
from mdbackup.config import CloudConfig


class ArchiveTests(TestCase):
    _actions = None

    def _run_task_actions(self, _, actions):
        self._actions = actions

    def _check_from_dir(self, folder):
        self.assertDictEqual({
            'from-directory': str(folder),
        }, self._actions[0])

    def _check_tar(self):
        self.assertDictEqual({
            'tar': None,
        }, self._actions[1])

    def _check_to_file(self, folder, backup_path, ext='', num=2):
        self.assertDictEqual({
            'to-file': {
                'to': folder.parts[-1] + '.tar' + ext,
                '_backup_path': backup_path,
            },
        }, self._actions[num])

    def setUp(self):
        super().setUp()
        register()

    def tearDown(self):
        super().tearDown()
        _clean_actions()

    @patch('mdbackup.archive.run_task_actions')
    def test_no_compression_no_encrypt_should_run_actions_to_create_a_tar_file(self, mock: Mock):
        config = CloudConfig({'providers': []})
        backup_path = Path()
        folder = backup_path / 'folder'
        mock.side_effect = self._run_task_actions

        archive_folder(backup_path, folder, config)

        self.assertIsNotNone(self._actions)
        self.assertEqual(3, len(self._actions))
        self._check_from_dir(folder)
        self._check_tar()
        self._check_to_file(folder, backup_path)

    @patch('mdbackup.archive.run_task_actions')
    def test_compression_no_encrypt_should_run_actions_to_create_a_tar_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'compression': {'method': 'br'}})
        backup_path = Path()
        folder = backup_path / 'folder'
        mock.side_effect = self._run_task_actions

        archive_folder(backup_path, folder, config)

        self.assertIsNotNone(self._actions)
        self.assertEqual(4, len(self._actions))
        self._check_from_dir(folder)
        self._check_tar()
        self.assertDictEqual({
            'compress-br': {
                'level': 6,
            },
        }, self._actions[2])
        self._check_to_file(folder, backup_path, '.br', 3)

    @patch('mdbackup.archive.run_task_actions')
    def test_no_compression_encrypt_should_run_actions_to_create_a_tar_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'cypher': {'strategy': 'gpg-passphrase', 'passphrase': '1'}})
        backup_path = Path()
        folder = backup_path / 'folder'
        mock.side_effect = self._run_task_actions

        archive_folder(backup_path, folder, config)

        self.assertIsNotNone(self._actions)
        self.assertEqual(4, len(self._actions))
        self._check_from_dir(folder)
        self._check_tar()
        self.assertDictEqual({
            'encrypt-gpg': {
                'passphrase': '1',
                'recipients': [],
                'algorithm': None,
            },
        }, self._actions[2])
        self._check_to_file(folder, backup_path, '.asc', 3)

    @patch('mdbackup.archive.run_task_actions')
    def test_compression_encrypt_should_run_actions_to_create_a_tar_file(self, mock: Mock):
        config = CloudConfig({
            'providers': [],
            'cypher': {'strategy': 'gpg-passphrase', 'passphrase': '1'},
            'compression': {'method': 'gzip'},
        })
        backup_path = Path()
        folder = backup_path / 'folder'
        mock.side_effect = self._run_task_actions

        archive_folder(backup_path, folder, config)

        self.assertIsNotNone(self._actions)
        self.assertEqual(5, len(self._actions))
        self._check_from_dir(folder)
        self._check_tar()
        self.assertDictEqual({
            'compress-gzip': {
                'level': 6,
            },
        }, self._actions[2])
        self.assertDictEqual({
            'encrypt-gpg': {
                'passphrase': '1',
                'recipients': [],
                'algorithm': None,
            },
        }, self._actions[3])
        self._check_to_file(folder, backup_path, '.gzip.asc', 4)
