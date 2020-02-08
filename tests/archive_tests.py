from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from mdbackup.actions.builtin._register import register
from mdbackup.actions.container import _clean_actions
from mdbackup.archive import archive_file, archive_folder
from mdbackup.config import CloudConfig


class ArchiveFolderTests(TestCase):
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
        config = CloudConfig({'providers': [], 'compression': {'method': 'br', 'cpus': 2}})
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
                'cpus': 2,
            },
        }, self._actions[2])
        self._check_to_file(folder, backup_path, '.br', 3)

    @patch('mdbackup.archive.run_task_actions')
    def test_no_compression_encrypt_should_run_actions_to_create_a_tar_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'encrypt': {'strategy': 'gpg-passphrase', 'passphrase': '1'}})
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
            'encrypt': {'strategy': 'gpg-passphrase', 'passphrase': '1'},
            'compression': {'method': 'gz'},
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
            'compress-gz': {
                'level': 6,
                'cpus': None,
            },
        }, self._actions[2])
        self.assertDictEqual({
            'encrypt-gpg': {
                'passphrase': '1',
                'recipients': [],
                'algorithm': None,
            },
        }, self._actions[3])
        self._check_to_file(folder, backup_path, '.gz.asc', 4)


class ArchiveFileTests(TestCase):
    _actions = None

    def _run_task_actions(self, _, actions):
        self._actions = actions

    def _generate_actions(self, compressed=False, encrypted=False):
        actions = [{'from-file': None}]
        if compressed:
            actions.append({'compress-xd': None})
        if encrypted:
            actions.append({'encrypt-asd': None})
        actions.append({'to-file': None})
        return {'actions': actions}

    def _check_from_file(self, file_path):
        self.assertDictEqual({
            'from-file': str(file_path),
        }, self._actions[0])

    def _check_to_file(self, file_path, backup_path, ext='', num=2):
        self.assertDictEqual({
            'to-file': {
                'to': file_path.parts[-1] + ext,
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
    def test_no_compression_no_encrypt_should_not_run_actions_and_return_none(self, mock: Mock):
        config = CloudConfig({'providers': []})
        task = self._generate_actions()
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNone(self._actions)
        self.assertIsNone(filename)

    @patch('mdbackup.archive.run_task_actions')
    def test_compression_no_encrypt_with_no_compressed_file_should_run_actions_to_create_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'compression': {'method': 'br', 'cpus': 2}})
        task = self._generate_actions()
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNotNone(filename)
        self.assertIsNotNone(self._actions)
        self.assertEqual(3, len(self._actions))
        self._check_from_file(path)
        self.assertDictEqual({
            'compress-br': {
                'level': 6,
                'cpus': 2,
            },
        }, self._actions[1])
        self._check_to_file(path, backup_path, '.br', 2)

    @patch('mdbackup.archive.run_task_actions')
    def test_compression_no_encrypt_with_compressed_file_should_do_nothing(self, mock: Mock):
        config = CloudConfig({'providers': [], 'compression': {'method': 'br', 'cpus': 2}})
        task = self._generate_actions(compressed=True)
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNone(filename)
        self.assertIsNone(self._actions)

    @patch('mdbackup.archive.run_task_actions')
    def test_no_compression_encrypt_with_no_encrypted_file_should_run_actions_to_create_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'encrypt': {'strategy': 'gpg-passphrase', 'passphrase': '1'}})
        task = self._generate_actions()
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNotNone(filename)
        self.assertIsNotNone(self._actions)
        self.assertEqual(3, len(self._actions))
        self._check_from_file(path)
        self.assertDictEqual({
            'encrypt-gpg': {
                'passphrase': '1',
                'recipients': [],
                'algorithm': None,
            },
        }, self._actions[1])
        self._check_to_file(path, backup_path, '.asc', 2)

    @patch('mdbackup.archive.run_task_actions')
    def test_no_compression_encrypt_with_encrypted_file_should_run_actions_to_create_file(self, mock: Mock):
        config = CloudConfig({'providers': [], 'encrypt': {'strategy': 'gpg-passphrase', 'passphrase': '1'}})
        task = self._generate_actions(encrypted=True)
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNone(filename)
        self.assertIsNone(self._actions)

    @patch('mdbackup.archive.run_task_actions')
    def test_compression_encrypt_should_run_actions_to_create_file(self, mock: Mock):
        config = CloudConfig({
            'providers': [],
            'encrypt': {'strategy': 'gpg-passphrase', 'passphrase': '1'},
            'compression': {'method': 'gz'},
        })
        task = self._generate_actions()
        backup_path = Path()
        path = backup_path / 'file.txt'
        mock.side_effect = self._run_task_actions

        filename = archive_file(backup_path, path, task, config)

        self.assertIsNotNone(filename)
        self.assertIsNotNone(self._actions)
        self.assertEqual(4, len(self._actions))
        self._check_from_file(path)
        self.assertDictEqual({
            'compress-gz': {
                'level': 6,
                'cpus': None,
            },
        }, self._actions[1])
        self.assertDictEqual({
            'encrypt-gpg': {
                'passphrase': '1',
                'recipients': [],
                'algorithm': None,
            },
        }, self._actions[2])
        self._check_to_file(path, backup_path, '.gz.asc', 3)
