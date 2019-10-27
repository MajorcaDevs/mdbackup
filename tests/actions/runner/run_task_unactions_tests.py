from io import FileIO
from subprocess import Popen
from unittest.mock import MagicMock, Mock

from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.container import _clean_actions, register_action
from mdbackup.actions.runner import run_task_unactions


def _failure_impl(_1, _2):
    raise KeyError('f')


def _register_actions(this=None):
    def nop():
        pass
    if this is not None:
        this._initial_stream_mock = Mock(spec=FileIO)
        this._middle_stream_mock = Mock(spec=Popen)
        this._middle_stream_mock.stdout = MagicMock(spec=FileIO)
        this._middle_stream_mock.stderr = MagicMock(spec=FileIO)
        this._middle_stream_mock.wait.return_value = 0
        register_action('final', nop, lambda _1, _2: this._initial_stream_mock, expected_input='stream')
        register_action('middle', nop, lambda _, _2: this._middle_stream_mock, expected_input='stream', output='stream')
    else:
        register_action('final', nop, lambda _1, _2: None, expected_input='stream')
        register_action('middle', nop, lambda _1, _2: None, expected_input='stream', output='stream')
    register_action('initial', nop, lambda _1, _2: None, output='stream')
    register_action('initial-with-no-unaction', nop)
    register_action('ifailure', nop, _failure_impl, output='stream')
    register_action('ffailure', nop, _failure_impl, expected_input='stream')
    register_action('bad', nop, lambda _1, _2: [], output='stream')


class RunTaskUnactionsWithNoActionsTests(TestCaseWithoutLogs):
    def setUp(self):
        super().setUp()
        _register_actions()

    def tearDown(self):
        super().tearDown()
        _clean_actions()

    def test_run_unactions_should_work(self):
        run_task_unactions('test', [])


class RunTaskUnactionsWithOneActionTests(TestCaseWithoutLogs):
    def setUp(self):
        super().setUp()
        _register_actions()

    def tearDown(self):
        super().tearDown()
        _clean_actions()

    def test_run_unactions_should_work(self):
        actions = [{'final': 1}]

        run_task_unactions('test', actions)

    def test_run_unactions_with_incompatible_action_should_fail(self):
        actions = [{'initial': 1}]

        with self.assertRaises(Exception):
            run_task_unactions('test', actions)

    def test_run_unactions_with_action_without_unaction_should_fail(self):
        actions = [{'initial-with-no-unaction': 1}]

        with self.assertRaises(Exception):
            run_task_unactions('test', actions)

    def test_run_unactions_with_action_failing_should_raise_the_exception(self):
        actions = [{'ffailure': 1}]

        with self.assertRaisesRegex(KeyError, r'f'):
            run_task_unactions('test', actions)

    def test_run_unactions_with_unexisting_action_should_fail(self):
        actions = [{'nope': None}]

        with self.assertRaises(KeyError):
            run_task_unactions('test', actions)


class RunTaskUnactionsWithMultipleActionsTests(TestCaseWithoutLogs):
    _initial_stream_mock = None
    _middle_stream_mock = None

    def setUp(self):
        super().setUp()
        _register_actions(self)

    def tearDown(self):
        super().tearDown()
        _clean_actions()

    def test_run_unactions_should_work(self):
        actions = [{'initial': 1}, {'final': 2}]

        run_task_unactions('test', actions)

    def test_run_unactions_should_dispose_streams(self):
        actions = [{'initial': 1}, {'final': 2}]

        run_task_unactions('test', actions)

        self._initial_stream_mock.close.assert_called_once()

    def test_run_unactions_with_action_failing_should_raise_the_exception(self):
        actions = [{'initial': 1}, {'ffailure': 2}]

        with self.assertRaises(KeyError):
            run_task_unactions('test', actions)

    def test_run_unactions_with_bad_action_should_fail(self):
        actions = [{'bad': ':(', 'final': ':(('}]

        with self.assertRaises(Exception):
            run_task_unactions('test', actions)

    def test_run_unactions_should_work_2(self):
        actions = [{'initial': 1}, {'middle': 2}, {'final': 3}]

        run_task_unactions('test', actions)

    def test_run_unactions_should_wait_for_the_process(self):
        actions = [{'initial': 1}, {'middle': 2}, {'final': 3}]

        run_task_unactions('test', actions)

        self._initial_stream_mock.close.assert_called_once()
        self._middle_stream_mock.wait.assert_called_once()

    def test_run_unactions_should_fail_if_process_fails(self):
        actions = [{'initial': 1}, {'middle': 2}, {'final': 3}]
        self._middle_stream_mock.wait.return_value = 1

        with self.assertRaises(Exception):
            run_task_unactions('test', actions)

        self._middle_stream_mock.stderr.__iter__.assert_called()

    def test_run_unactions_should_kill_process_if_action_raises(self):
        actions = [{'ifailure': 1}, {'middle': 2}, {'final': 3}]

        with self.assertRaises(Exception):
            run_task_unactions('test', actions)

        self._middle_stream_mock.send_signal.assert_called_once()
