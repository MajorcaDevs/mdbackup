from io import BufferedIOBase, FileIO, TextIOBase
from subprocess import Popen
from types import GeneratorType
from unittest.mock import Mock

from tests.classes import TestCaseWithoutLogs

from mdbackup.actions.runner import _process_output


def _mock_process():
    mock = Mock(spec=Popen)
    mock.stdout = 'process:stdout'
    return mock


def _mock_text_io_stream(bad=False):
    mock = Mock(spec=TextIOBase)
    mock.buffer = _mock_buffered_io_stream(bad)
    return mock


def _mock_buffered_io_stream(bad=False):
    mock = Mock(spec=BufferedIOBase)
    mock.raw = None if bad else _mock_raw_stream()
    return mock


def _mock_raw_stream():
    return Mock(spec=FileIO)


def _mock_dir_entry_generator():
    return ('flase' for i in range(0, 1))


class ProccessOutputTests(TestCaseWithoutLogs):
    def test_should_fail_with_unsupported_output(self):
        with self.assertRaisesRegex(Exception, r'Unsupported output type <.*?> for \w+'):
            _process_output(None, 'test')

    def test_should_return_stdout_for_a_process_output(self):
        mock = _mock_process()

        prev_input, (output, action_key) = _process_output(mock, 'test')

        self.assertEqual('process:stdout', prev_input)
        self.assertIsInstance(output, Popen)
        self.assertEqual(mock, output)
        self.assertEqual('test', action_key)

    def test_should_return_raw_stream_for_a_text_stream_output(self):
        mock = _mock_text_io_stream()

        prev_input, (output, action_key) = _process_output(mock, 'test')

        self.assertIsInstance(prev_input, FileIO)
        self.assertIsInstance(output, TextIOBase)
        self.assertEqual(mock, output)
        self.assertEqual('test', action_key)

    def test_should_raise_if_text_stream_does_not_point_to_a_file_io(self):
        mock = _mock_text_io_stream(bad=True)

        with self.assertRaisesRegex(IOError, r'.+must contain a io.FileIO.+'):
            _process_output(mock, 'test')

    def test_should_return_raw_stream_for_a_buffered_raw_stream_output(self):
        mock = _mock_buffered_io_stream()

        prev_input, (output, action_key) = _process_output(mock, 'test')

        self.assertIsInstance(prev_input, FileIO)
        self.assertIsInstance(output, BufferedIOBase)
        self.assertEqual(mock, output)
        self.assertEqual('test', action_key)

    def test_should_raise_if_buffered_raw_stream_does_not_point_to_a_file_io(self):
        mock = _mock_buffered_io_stream(bad=True)

        with self.assertRaisesRegex(IOError, r'.+must contain a io.FileIO.+'):
            _process_output(mock, 'test')

    def test_should_return_raw_stream_for_a_raw_stream_output(self):
        mock = _mock_raw_stream()

        prev_input, (output, action_key) = _process_output(mock, 'test')

        self.assertIsInstance(prev_input, FileIO)
        self.assertIsInstance(output, FileIO)
        self.assertEqual(mock, output)
        self.assertEqual(mock, prev_input)
        self.assertEqual('test', action_key)

    def test_should_return_the_generator_for_a_generator_output(self):
        mock = _mock_dir_entry_generator()

        prev_input, tup = _process_output(mock, 'test')

        self.assertIsInstance(prev_input, GeneratorType)
        self.assertIsNone(tup)
