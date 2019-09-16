import logging
from unittest import TestCase


class TestCaseWithoutLogs(TestCase):
    @classmethod
    def setUpClass(cls):
        logging.disable(logging.CRITICAL)
        return super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        logging.disable(logging.NOTSET)
        return super().tearDownClass()
