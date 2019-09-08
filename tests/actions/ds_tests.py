from pathlib import Path
from unittest import TestCase

from mdbackup.actions.ds import DirEntry


class DirEntryTests(TestCase):
    def test_from_real_path_of_a_folder_is_filled_correctly(self):
        path = Path('./tests')

        entry = DirEntry.from_real_path(path)

        self.assertEqual('dir', entry.type)
        self.assertEqual(Path('./tests'), entry.path)
        self.assertIsNotNone(entry.stats)
        self.assertIsNone(entry.link_content)
        self.assertIsNone(entry.stream)

    def test_from_real_path_of_a_folder_is_filled_correctly_having_a_root_path(self):
        path = Path('./tests/actions')
        root_path = Path('./tests')

        entry = DirEntry.from_real_path(path, root_path)

        self.assertEqual('dir', entry.type)
        self.assertEqual(Path('./actions'), entry.path)
        self.assertIsNotNone(entry.stats)
        self.assertIsNone(entry.link_content)
        self.assertIsNone(entry.stream)

    def test_from_real_path_of_a_file_is_filled_correctly(self):
        path = Path('./tests/__init__.py')

        entry = DirEntry.from_real_path(path)

        self.assertEqual('file', entry.type)
        self.assertEqual(Path('./tests/__init__.py'), entry.path)
        self.assertIsNotNone(entry.stats)
        self.assertIsNone(entry.link_content)
        self.assertIsNotNone(entry.stream)
        self.assertEqual(b'', b'\n'.join(entry.stream.readlines()))

        entry.stream.close()

    def test_from_real_path_of_a_symlink_is_filled_correctly(self):
        path = Path('./docs/README.md')

        entry = DirEntry.from_real_path(path)

        self.assertEqual('symlink', entry.type)
        self.assertEqual(Path('./docs/README.md'), entry.path)
        self.assertIsNotNone(entry.stats)
        self.assertEqual('../README.md', entry.link_content)
        self.assertIsNone(entry.stream)

    def test_from_real_path_of_an_invalid_file_type_should_raise_typeerror(self):
        path = Path('/dev/stdout').resolve()

        with self.assertRaises(TypeError):
            DirEntry.from_real_path(path)
