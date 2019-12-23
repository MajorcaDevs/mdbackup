from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, get_unaction, register_action


class TestGetUnaction(TestCaseWithoutLogs):
    def setUp(self):
        register_action(
            'very-specific-action',
            action=lambda _1, _2: True,
            unaction=lambda _1, _2: 'yes',
            output='directory',
        )
        register_action(
            'very-specific-action-with-no-unaction',
            action=lambda _1, _2: True,
            output='directory',
        )
        return super().setUp()

    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_get_existing_unaction_should_return_the_function(self):
        res = get_unaction('very-specific-action')

        self.assertTrue(callable(res))
        self.assertEqual('yes', res(None, None))

    def test_get_existing_action_but_without_unaction_should_return_the_none(self):
        res = get_unaction('very-specific-action-with-no-unaction')

        self.assertIsNone(res)

    def test_get_non_existing_unaction_should_raise_keyerror(self):
        with self.assertRaises(KeyError):
            get_unaction('almost-an-action')

    def test_unaction_is_case_sensitive(self):
        with self.assertRaises(KeyError):
            get_unaction('Very-Specific-Action')
        with self.assertRaises(KeyError):
            get_unaction('Very-Specific-Action-With-No-Unaction')
