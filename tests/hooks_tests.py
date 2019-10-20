from unittest.mock import call, Mock, patch

from tests.classes import TestCaseWithoutLogs

from mdbackup.hooks import _hooks_config, define_hook, run_hook


class HookTests(TestCaseWithoutLogs):
    hook_1_cmd = 'bash -c \'echo This is the hook #1\''
    hook_2_cmd = 'bash -c \'echo this-is-the-hook-#2 | tr - " "\''
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
        run_hook('hook-0')

    @patch('mdbackup.hooks._hook_runner')
    def test_not_defined_hook_should_not_run_anything(self, hooks_runner_mock: Mock):
        run_hook('hook-0')

        hooks_runner_mock.assert_not_called()

    @patch('mdbackup.hooks._hook_runner')
    def test_defined_hook_should_run_successfully(self, hooks_runner_mock: Mock):
        hooks_runner_mock.return_value = lambda: None

        run_hook('hook-2')

        self.assertEqual(2, hooks_runner_mock.call_count)
        hooks_runner_mock.assert_has_calls([
            call('hook-2', self.hook_2_cmd, 'hook-2', cwd=None, shell=True),
            call('hook-2', self.hook_ii_cmd, 'hook-2', cwd=None, shell=True),
        ])

    @patch('mdbackup.hooks._hook_runner')
    def test_with_non_existing_cwd_should_not_run_hooks(self, hooks_runner_mock: Mock):
        run_hook('hook-1', cwd='tests/non-existing-folder')

        hooks_runner_mock.assert_not_called()

    @patch('mdbackup.hooks._hook_runner')
    def test_with_cwd_not_being_a_directory_should_not_run_hooks(self, hooks_runner_mock: Mock):
        run_hook('hook-1', cwd='tests/hooks_tests.py')

        hooks_runner_mock.assert_not_called()

    @patch('mdbackup.hooks._hook_runner')
    def test_defined_hook_with_valid_cwd_should_run_successfully(self, hooks_runner_mock: Mock):
        hooks_runner_mock.return_value = lambda: None

        run_hook('hook-2', cwd='tests')

        self.assertEqual(2, hooks_runner_mock.call_count)
        hooks_runner_mock.assert_has_calls([
            call('hook-2', self.hook_2_cmd, 'hook-2', cwd='tests', shell=True),
            call('hook-2', self.hook_ii_cmd, 'hook-2', cwd='tests', shell=True),
        ])

    def test_real_test_on_hook_should_not_fail(self):
        run_hook('hook-1', cwd='tests')
