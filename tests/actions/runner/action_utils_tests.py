from tests.classes import TestCase, TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, register_action
from mdbackup.actions.runner import (
    _check_for_incompatible_actions,
    _get_action_from_definition,
    _get_action_key_from_definition,
)


class GetActionKeyFromDefinitionTests(TestCase):
    def test_should_return_the_first_key_of_the_action_definition_dict(self):
        action_def = {'test-action': False}

        key = _get_action_key_from_definition(action_def)

        self.assertEqual('test-action', key)


class GetActionFromDefinitionTests(TestCaseWithoutLogs):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_action('test-action', lambda: None, expected_input='stream')

    @classmethod
    def tearDownClass(cls):
        _clean_actions()
        super().tearDownClass()

    def test_should_return_the_action_the_params_and_the_key_of_the_action_definition_dict(self):
        action_def = {'test-action': 'yes'}

        action, params, key = _get_action_from_definition(action_def)

        self.assertTrue(callable(action))
        self.assertIsNone(action())
        self.assertEqual('yes', params)
        self.assertEqual('test-action', key)


class CheckForIncompatibleActionsTests(TestCaseWithoutLogs):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        register_action('final-action', lambda: None, expected_input='stream')
        register_action('initial-action', lambda: None, output='stream')

    @classmethod
    def tearDownClass(cls):
        _clean_actions()
        super().tearDownClass()

    def test_should_pass_if_actions_is_empty(self):
        actions = []

        _check_for_incompatible_actions(actions)

    def test_should_pass_if_actions_are_compatible(self):
        actions = [
            {'initial-action': 'yes'},
            {'final-action': 'no'},
        ]

        _check_for_incompatible_actions(actions)

    def test_should_raise_if_actions_are_incompatible(self):
        actions = [
            {'final-action': 'no'},
            {'initial-action': 'yes'},
        ]

        with self.assertRaises(Exception):
            _check_for_incompatible_actions(actions)

    def test_should_raise_if_final_action_has_output(self):
        actions = [
            {'initial-action': 'maybe'},
        ]

        with self.assertRaises(Exception):
            _check_for_incompatible_actions(actions)
