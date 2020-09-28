from unittest.mock import call, Mock, patch

from tests.classes import TestCaseWithoutLogs

from mdbackup.hooks import _hooks_config, define_hook, run_hook


class HookTests(TestCaseWithoutLogs):
    hook_1_cmd = 'bash -c \'echo "This is the hook #1"; echo it is indeed >&2; cat\''
    hook_2_cmd = 'bash -c \'echo "this-is-the-hook-#2" | tr - " "\''
    hook_ii_cmd = 'bash -c \'printf "%s%n" "This is not the hook #2"\''

    def setUp(self):
        super().setUp()
        define_hook('hook-1', self.hook_1_cmd)
        define_hook('hook-2', self.hook_2_cmd)
        define_hook('hook-2', self.hook_ii_cmd)

    def tearDown(self):
        super().tearDown()
        _hooks_config.clear()

    def test_not_defined_hook_should_not_fail(self):
        run_hook('hook-0', {})

    @patch('mdbackup.hooks._hook_runner')
    def test_not_defined_hook_should_not_run_anything(self, hooks_runner_mock: Mock):
        run_hook('hook-0', {})

        hooks_runner_mock.assert_not_called()

    @patch('mdbackup.hooks._hook_runner')
    def test_defined_hook_should_run_successfully(self, hooks_runner_mock: Mock):
        hooks_runner_mock.return_value = lambda: None

        run_hook('hook-2', {})

        self.assertEqual(2, hooks_runner_mock.call_count)
        hooks_runner_mock.assert_has_calls([
            call('hook-2', self.hook_2_cmd, '{}'),
            call('hook-2', self.hook_ii_cmd, '{}'),
        ])

    def test_real_test_on_hook_should_not_fail(self):
        run_hook('hook-1', {'json': 'yes', 'complex': ['very', 'indeed']})
