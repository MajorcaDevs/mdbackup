from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, register_action


class TestRegisterAction(TestCaseWithoutLogs):
    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_register_correct_action_should_pass(self):
        register_action(
            'ab',
            lambda _1, _2: None,
            lambda _1, _2: False,
            None,
            'stream',
        )

    def test_register_with_duplicated_key_should_raise_keyerror(self):
        register_action(
            'ab',
            lambda _1, _2: None,
            output='stream',
        )

        with self.assertRaises(KeyError):
            register_action(
                'ab',
                lambda _1, _2: True,
                expected_input='stream',
            )

    def test_register_with_invalid_identifier_should_raise_keyerror(self):
        keys = ['a', '9-the-best', '(yes)', '_123-yes.']
        for i, key in zip(range(len(keys)), keys):
            with self.subTest(i=i):
                with self.assertRaises(KeyError):
                    register_action(
                        key,
                        lambda _1, _2: True,
                        expected_input='stream',
                    )

    def test_register_with_invalid_expected_input_should_raise_valueerror(self):
        with self.assertRaises(ValueError):
            register_action(
                'good-key',
                lambda _1, _2: True,
                expected_input='unexpected',
            )

    def test_register_with_invalid_output_should_raise_valueerror(self):
        with self.assertRaises(ValueError):
            register_action(
                'good-key',
                lambda _1, _2: True,
                output='unexpected',
            )

    def test_register_without_expected_input_nor_output_should_work(self):
        register_action('good-key', lambda _1, _2: True)

    def test_register_with_a_non_callable_action_should_raise_typeerror(self):
        with self.assertRaises(TypeError):
            register_action('good-key', [], output='directory')

    def test_register_with_a_non_callable_unaction_should_raise_typeerror(self):
        with self.assertRaises(TypeError):
            register_action(
                'good-key',
                action=lambda _1, _2: True,
                unaction=[],
                output='directory',
            )
