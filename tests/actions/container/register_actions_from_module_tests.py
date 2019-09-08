from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, register_actions_from_module


def fake_register_function(**kwargs):
    if 'register_action' not in kwargs:
        raise KeyError('register_action')
    if 'get_action' not in kwargs:
        raise KeyError('get_action')
    if 'get_unaction' not in kwargs:
        raise KeyError('get_unaction')


class RegisterActionsFromModuleTests(TestCaseWithoutLogs):
    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_register_with_correct_module_and_function_should_work(self):
        register_actions_from_module(
            'tests.actions.container.register_actions_from_module_tests#fake_register_function',
        )

    def test_register_with_incorrect_full_thing_should_raise_valueerror(self):
        with self.assertRaises(ValueError):
            register_actions_from_module('f')
        with self.assertRaises(ValueError):
            register_actions_from_module('f#1#2')

    def test_register_with_non_existing_module_should_raise_modulenotfounderror(self):
        with self.assertRaises(ModuleNotFoundError):
            register_actions_from_module('tests.actions.container.nope#fake_register_function')

    def test_register_with_non_existing_function_should_raise_attributeerror(self):
        with self.assertRaises(AttributeError):
            register_actions_from_module('tests.actions.container.register_actions_from_module_tests#no')
