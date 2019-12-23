import itertools

from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, are_compatible, register_action


actions = [
    ('no-input-directory-output', None, 'directory'),
    ('no-input-stream-output', None, 'stream'),
    ('stream-input-stream-output', 'stream', 'stream'),
    ('stream-input-directory-output', 'stream', 'directory'),
    ('directory-input-stream-output', 'directory', 'stream'),
    ('directory-input-directory-output', 'directory', 'directory'),
    ('stream-input-no-output', 'stream', None),
    ('directory-input-no-output', 'directory', None),
]

action_pairs = list(itertools.combinations(actions, 2))
compatible_pairs = [(action1[0], action2[0]) for action1, action2 in action_pairs if action1[2] == action2[1]]
incompatible_pairs = [(action1[0], action2[0]) for action1, action2 in action_pairs if action1[2] != action2[1]]


class TestAreCompatible(TestCaseWithoutLogs):
    def setUp(self):
        for action, _input, output in actions:
            register_action(action, lambda _1, _2: True, expected_input=_input, output=output)
        return super().setUp()

    def tearDown(self):
        _clean_actions()
        return super().tearDown()

    def test_compatible_actions_should_return_none(self):
        for i, (input_action, output_action) in zip(range(len(compatible_pairs)), compatible_pairs):
            with self.subTest(i=i, input_action=input_action, output_action=output_action):
                res = are_compatible(input_action, output_action)
                self.assertIsNone(res)

    def test_incompatible_actions_should_return_string(self):
        for i, (input_action, output_action) in zip(range(len(incompatible_pairs)), incompatible_pairs):
            with self.subTest(i=i, input_action=input_action, output_action=output_action):
                res = are_compatible(input_action, output_action)
                self.assertIsInstance(res, str)

    def test_should_raise_keyerror_if_action_does_not_exist(self):
        with self.assertRaises(KeyError):
            are_compatible('a', actions[0][0])
        with self.assertRaises(KeyError):
            are_compatible(actions[0][0], 'b')
