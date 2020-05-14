import unittest

from parameterized import parameterized
from hamcrest import *
from mock import Mock

from general.scans.defaults import Defaults
from general.scans.motion import Motion


class TestDefaults(Defaults):

    @staticmethod
    def log_file(info):
        return "{}".format(info["action_title"])

    @staticmethod
    def detector(**kwargs):
        pass


class TestSpectrasWithTimeRange(unittest.TestCase):

    def test_GIVEN_scan_with_action_WHEN_get_log_file_THEN_log_file_returned_with_action_title(self):

        myscan = TestDefaults()
        expected_block_name = "block_name"
        scan = myscan.scan(Motion(Mock(return_value=1), None, expected_block_name), 0, 1, 1)

        file_name = myscan.log_file(scan.log_file_info())

        assert_that(file_name, is_(expected_block_name))


if __name__ == '__main__':
    unittest.main()
