from io import StringIO
import os
from unittest import TestCase

from mdbackup.jsonschemavalidator import validate


class JsonSchemaValidatorTests(TestCase):
    _output: StringIO
    _schema_path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)),
        '..',
        'mdbackup',
        'json-schemas',
        'config.schema.json',
    )

    def setUp(self):
        super().setUp()
        self._output = StringIO()

    def test_validation_with_valid_data_should_pass_validation(self):
        ret = validate(self._schema_path, {
            'backupsPath': '/',
            'env': {},
        }, self._output)

        self.assertTrue(ret)
        self.assertEqual('', self._output.getvalue())

    def test_validation_with_invalid_data_should_fail_validation(self):
        ret = validate(self._schema_path, {
            'backupsPath': '/',
            'cloud': {
                'providers': [
                    {'type': 'xd'},
                ],
            },
        }, self._output)
        lines = self._output.getvalue()[:-1].split('\n')

        self.assertFalse(ret)
        self.assertNotEqual(0, len(self._output.getvalue()))
        self.assertEqual(3, len(lines))
        self.assertEqual('- : \'env\' is a required property', lines[0])
        self.assertEqual('- cloud.providers[0]: \'backupsPath\' is a required property', lines[1])
        self.assertEqual('- cloud.providers[0]: {\'type\': \'xd\'} is not valid under any of the given schemas',
                         lines[2])
