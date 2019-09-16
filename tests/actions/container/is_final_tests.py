from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, is_final, register_action


class IsFinalCompatible(TestCaseWithoutLogs):
    def setUp(self):
        register_action('final', lambda _1, _2: True, expected_input='stream')
        register_action('non-final', lambda _1, _2: True, expected_input='stream', output='stream')
        return super().setUp()

    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_is_final_should_return_true_if_action_has_no_output(self):
        action = 'final'

        result = is_final(action)

        self.assertTrue(result)

    def test_is_final_should_return_false_if_action_has_output(self):
        action = 'non-final'

        result = is_final(action)

        self.assertFalse(result)
