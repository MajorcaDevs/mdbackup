from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, get_action, register_action


class TestGetAction(TestCaseWithoutLogs):
    def setUp(self):
        register_action('very-specific-action', lambda _1, _2: True, output='directory')
        return super().setUp()

    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_get_existing_action_should_return_the_function(self):
        res = get_action('very-specific-action')

        self.assertTrue(callable(res))
        self.assertTrue(res(None, None))

    def test_get_non_existing_action_should_raise_keyerror(self):
        with self.assertRaises(KeyError):
            get_action('almost-an-action')

    def test_action_is_case_sensitive(self):
        with self.assertRaises(KeyError):
            get_action('Very-Specific-Action')
