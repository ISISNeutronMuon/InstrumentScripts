import unittest
from contextlib import contextmanager

from hamcrest import *
from mock import Mock, patch

from general.scans.defaults import Defaults
from general.scans.monoid import Average
from general.scans.motion import Motion


class TestDefaults(Defaults):

    @staticmethod
    def log_file(info):
        return "{}".format(info["action_title"])

    @staticmethod
    def detector(acc, **kwargs):
        return acc, Average(1, 1)

    def get_fig(self):
        return Mock(), Mock()


MOCK_BLOCK_PREFIX = "INST:CS:BS:"


@contextmanager
def fake_block_server_and_get_pv(block_and_value):
    """
    Context which creates a fake block server by mocking out parts of genie

    Parameters
    ----------
    block_and_value: blocks and their initial values

    Returns
    -------
    nothing
    """
    block_history = []
    with patch("general.scans.motion.g.get_pv") as get_pv, \
            patch("general.scans.motion.g.adv.get_pv_from_block") as get_pv_from_block, \
            patch("general.scans.motion.g.__api") as api, \
            patch("general.scans.motion.g.get_blocks") as get_blocks, \
            patch("general.scans.motion.g.cget") as cget, \
            patch("general.scans.motion.g.cset") as cset:

        block_history.append(dict(block_and_value))
        get_blocks.return_value = list(block_and_value.keys())

        get_pv_from_block.side_effect = lambda pv: f"{MOCK_BLOCK_PREFIX}{pv}"

        def mock_cget(pv):
            try:
                return {"value": block_and_value[pv]}
            except KeyError:
                return None

        def mock_cset(pv, value):
            try:
                block_and_value[pv] = value
                block_history.append(dict(block_and_value))
            except KeyError:
                print("Block did not exist {}".format(pv))

        cget.side_effect = mock_cget
        cset.side_effect = mock_cset
        yield block_history


class TestScans(unittest.TestCase):

    def test_GIVEN_scan_with_action_WHEN_get_log_file_THEN_log_file_returned_with_action_title(self):

        myscan = TestDefaults()
        expected_block_name = "block_name"
        scan = myscan.scan(Motion(Mock(return_value=1), None, expected_block_name), 0, 1, 1)

        file_name = myscan.log_file(scan.log_file_info())

        assert_that(file_name, is_(expected_block_name))

    def test_GIVEN_block_name_WHEN_create_scan_THEN_scan_has_block_motion_with_pv_as_action(self):

        myscan = TestDefaults()
        expected_value = 1
        block_name = "block_name"

        with fake_block_server_and_get_pv({block_name: expected_value}):
            scan = myscan.scan(block_name, 0, 1, 1)
            result = scan.action()

        assert_that(result, is_(expected_value))

    def test_GIVEN_block_name_WHEN_create_rscan_THEN_scan_has_block_motion_with_pv_as_action(self):

        myscan = TestDefaults()
        expected_value = 1
        block_name = "block_name"

        with fake_block_server_and_get_pv({block_name: expected_value}):
            scan = myscan.rscan(block_name, 0, 1, 0.1)
            result = scan.action()

        assert_that(result, is_(expected_value))

    def test_GIVEN_block_name_WHEN_create_dscan_THEN_scan_sets_blocks_to_points_in_scan(self):

        myscan = TestDefaults()
        initial_value = 1
        after_value = 1.0
        block_name = "block_name"

        with fake_block_server_and_get_pv({block_name: initial_value}) as block_server, \
             patch("general.scans.motion.g.get_runstate") as get_runstate:
            get_runstate.return_value = "SETUP"
            myscan.dscan(block_name, 0, 1, 1, -1)
            result = [list(blocks.values())[0] for blocks in block_server]

        assert_that(result, contains_exactly(initial_value, float(initial_value), initial_value + after_value, initial_value))

    def test_GIVEN_block_name_WHEN_create_ascan_THEN_scan_block_set_to_last_position(self):

        myscan = TestDefaults()
        initial_value = 0.1
        expected_value = 1
        block_name = "block_name"

        blocks = {block_name: initial_value}
        with fake_block_server_and_get_pv(blocks), \
             patch("general.scans.motion.g.get_runstate") as get_runstate:
            get_runstate.return_value = "SETUP"
            scan = myscan.ascan(block_name, -1, expected_value, 1, -1)

        assert_that(blocks, has_entry(block_name, expected_value))


if __name__ == '__main__':
    unittest.main()
