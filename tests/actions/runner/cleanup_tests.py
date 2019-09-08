from subprocess import Popen, signal
from unittest.mock import Mock

from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.runner import _cleanup


def _mock_process(stderr=[], exit_code=0):
    mock = Mock(spec=Popen)
    mock.stderr = stderr if isinstance(stderr, list) else [stderr]
    mock.wait = Mock(return_value=exit_code)
    return mock


def _mock_file_like_object():
    mock = Mock()
    mock.close = Mock(return_value=lambda: None)
    return mock


class CleanupTests(TestCaseWithoutLogs):
    def test_nothing_to_cleanup_should_work(self):
        things = []

        _cleanup(things, False)

    def test_cleanup_a_file_like_object_should_work(self):
        things = [(_mock_file_like_object(), 'test')]

        with self.subTest(has_raised=False):
            _cleanup(things, False)
        with self.subTest(has_raised=True):
            _cleanup(things, True)

    def test_cleanup_a_success_process_should_work(self):
        things = [(_mock_process(), 'test')]

        with self.subTest(has_raised=False):
            _cleanup(things, False)
        with self.subTest(has_raised=True):
            _cleanup(things, True)

    def test_cleanup_a_failed_process_should_raise_exception(self):
        things = [(_mock_process(exit_code=1), 'test')]

        for has_raised in (False, True):
            with self.subTest(has_raised=has_raised):
                with self.assertRaises(RuntimeError):
                    _cleanup(things, has_raised)

    def test_cleanup_exception_raised_due_to_a_failed_process_should_contain_the_stderr(self):
        things = [(_mock_process(stderr=b'this didn\'t work :(\n', exit_code=2), 'test')]

        with self.assertRaisesRegex(RuntimeError, '.+this didn\'t work :\\(.+'):
            _cleanup(things, False)

    def test_cleanup_with_file_like_object_and_success_process_should_work(self):
        things = [
            (_mock_file_like_object(), 'test-1'),
            (_mock_process(), 'test-2'),
        ]

        with self.subTest(has_raised=False):
            _cleanup(things, False)
        with self.subTest(has_raised=True):
            _cleanup(things, True)

    def test_cleanup_with_failed_process_and_file_like_object_should_raise(self):
        things = [
            (_mock_process(exit_code=1), 'test-1'),
            (_mock_file_like_object(), 'test-2'),
        ]

        for has_raised in (False, True):
            with self.subTest(has_raised=has_raised):
                with self.assertRaises(RuntimeError):
                    _cleanup(things, has_raised)


class CleanupIntegrationTests(TestCaseWithoutLogs):
    def test_should_close_the_file_like_for_ending(self):
        mock = _mock_file_like_object()
        things = [(mock, 'test')]

        _cleanup(things, False)

        mock.close.assert_called_once()

    def test_should_wait_the_process_for_ending(self):
        mock = _mock_process()
        things = [(mock, 'test')]

        _cleanup(things, False)

        mock.wait.assert_called_once()

    def test_should_not_send_signal_if_has_raised_is_false(self):
        mock = _mock_process()
        things = [(mock, 'test')]

        _cleanup(things, False)

        self.assertEqual(0, mock.send_signal.call_count)

    def test_should_send_signal_if_has_raised_is_true(self):
        mock = _mock_process()
        things = [(mock, 'test')]

        _cleanup(things, True)

        mock.send_signal.assert_called_once_with(signal.SIGTERM)

    def test_cleanup_with_failed_process_and_file_like_object_should_also_close_the_file(self):
        things = [
            (_mock_process(exit_code=1), 'test-1'),
            (_mock_file_like_object(), 'test-2'),
        ]

        with self.assertRaises(RuntimeError):
            _cleanup(things, False)

        things[0][0].wait.assert_called_once()
        things[1][0].close.assert_called_once()
