from unittest import TestCase

from mdbackup.utils import change_keys, raise_if_type_is_incorrect, snakeify


class SnakeifyTests(TestCase):
    def test_should_convert_camelcase_into_snakecase(self):
        strings = [
            ('SnakeifyTests', 'snakeify_tests'),
            ('veryPowerfulKey', 'very_powerful_key'),
            ('ClassName_WithUnderscore', 'class_name_with_underscore'),
            ('nope', 'nope'),
        ]

        for key, expected in strings:
            with self.subTest(key=key):
                res = snakeify(key)
                self.assertEqual(expected, res)

    def test_snakecase_should_remain_the_same(self):
        key = 'snakecase_should_remain_the_same'

        res = snakeify(key)

        self.assertEqual(key, res)

    def test_convert_non_string_value_must_return_the_same_value(self):
        key = 128

        res = snakeify(key)

        self.assertEqual(key, res)


class ChangeKeysTests(TestCase):
    def test_should_convert_camelcase_keys_into_snakecase(self):
        dictionary = {
            'firstKey': 1,
            'secondKey': 2,
            'ThirdKey': 3,
        }
        expected_dictionary = {
            'first_key': 1,
            'second_key': 2,
            'third_key': 3,
        }

        res = change_keys(dictionary)

        self.assertDictEqual(expected_dictionary, res)

    def test_should_convert_recursively_the_dictionaries(self):
        dictionary = {
            'firstKey': {
                'secondKey': {
                    'thirdKey': True,
                },
            },
        }
        expected_dictionary = {
            'first_key': {
                'second_key': {
                    'third_key': True,
                },
            },
        }

        res = change_keys(dictionary)

        self.assertDictEqual(expected_dictionary, res)


class RaiseIfTypeIsIncorrectTests(TestCase):
    def test_should_not_raise_if_type_is_correct(self):
        obj = 'string'
        typ = str

        raise_if_type_is_incorrect(obj, typ, 'obj must be a string')

    def test_should_not_raise_if_object_is_none_but_not_required(self):
        obj = None
        typ = str

        raise_if_type_is_incorrect(obj, typ, 'obj must be a string')

    def test_should_raise_if_type_is_incorrect(self):
        obj = b'string?'
        typ = str

        with self.assertRaisesRegex(TypeError, 'obj must be a string'):
            raise_if_type_is_incorrect(obj, typ, 'obj must be a string')

    def test_should_raise_if_object_is_none_and_required(self):
        obj = None
        typ = str

        with self.assertRaisesRegex(TypeError, 'obj must be a string'):
            raise_if_type_is_incorrect(obj, typ, 'obj must be a string', required=True)
