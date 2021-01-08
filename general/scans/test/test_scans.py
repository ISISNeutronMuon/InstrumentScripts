import unittest
from contextlib import contextmanager

from general.scans.scans import SimpleScan, ReplayScan
from hamcrest import *
from mock import Mock, patch, mock_open

from general.scans.defaults import Defaults
from general.scans.monoid import Average
from general.scans.motion import Motion

def test_map_function(x):
    return 2.0 * x


class ScanTests(unittest.TestCase):
    """
    Tests for the Scan classes
    """

    def test_GIVEN_simple_scan_class_WHEN_map_applied_THEN_new_class_has_mapped_values_in_container(self):
        initial_values = [1., 2., 3.]

        simple_scan = SimpleScan('action', initial_values, 'defaults')

        mapped_simple_scan = simple_scan.map(test_map_function)

        self.assertFalse(isinstance(mapped_simple_scan.values, map))

        for initial_value, mapped_value in zip(initial_values, mapped_simple_scan.values):
            self.assertEqual(test_map_function(initial_value), mapped_value)

    def test_GIVEN_replay_scan_class_WHEN_map_applied_THEN_new_class_has_mapped_values_in_container(self):
        xs = [1., 2., 3.]
        ys = [1., 4., 9.]
        axis = 1
        result = 'result'
        defaults = 'defaults'

        replay_scan = ReplayScan(xs, ys, axis, result, defaults)

        mapped_replay_scan = replay_scan.map(test_map_function)

        self.assertFalse(isinstance(mapped_replay_scan.xs, map))

        for initial_value, mapped_value in zip(xs, mapped_replay_scan.xs):
            self.assertEqual(test_map_function(initial_value), mapped_value)


class TestDefaults(Defaults):

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
            patch("general.scans.motion.g._genie_api") as api, \
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

    @patch("general.scans.defaults.g.get_script_dir", return_value="")
    def test_GIVEN_scan_with_action_WHEN_get_log_file_THEN_log_file_returned_with_action_title(self, get_script_dir):

        myscan = TestDefaults()
        expected_block_name = "block_name"
        scan = myscan.scan(Motion(Mock(return_value=1), None, expected_block_name), 0, 1, 1)

        file_name = myscan.log_file(scan.log_file_info())

        assert_that(file_name, contains_string(expected_block_name))

    def test_GIVEN_scan_with_action_WHEN_get_log_file_THEN_log_file_returned_with_genie_script_dir_path(self):

        myscan = TestDefaults()
        genie_script_path = "script/path"

        scan = myscan.scan(Motion(Mock(return_value=1), None, "block"), 0, 1, 1)

        with patch("general.scans.defaults.g.get_script_dir") as get_script_dir:
            get_script_dir.return_value = genie_script_path
            file_name = myscan.log_file(scan.log_file_info())

        assert_that(file_name, starts_with(genie_script_path))


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

    @patch("general.scans.defaults.g.get_script_dir", return_value="")
    def test_GIVEN_block_name_WHEN_create_dscan_THEN_scan_sets_blocks_to_points_in_scan(self, get_script_dir):

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

    @patch("general.scans.defaults.g.get_script_dir", return_value="")
    def test_GIVEN_block_name_WHEN_create_ascan_THEN_scan_block_set_to_last_position(self, get_script_dir):

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

    @patch("general.scans.defaults.g.get_script_dir")
    def test_GIVEN_replay_scan_WHEN_request_THEN_data_loaded_from_log_file_dir(self, get_script_dir):
        expected_script_dir = "scripting\\dir"
        get_script_dir.return_value = expected_script_dir

        myscan = TestDefaults()
        with patch("os.listdir") as listdir, \
            patch("os.path.getctime", return_value=1),\
                patch("builtins.open", mock_open(read_data='head1\thead2\thead3\n1\t1\t1\n1\t1\t1\n')) as open:

            listdir.return_value = ["file.dat"]
            myscan.last_scan()

            listdir.assert_called_with(expected_script_dir)

    @patch("general.scans.defaults.g.get_script_dir")
    def test_GIVEN_replay_scan_WHEN_request_but_no_files_in_dir_THEN_value_error_with_good_issue(self, get_script_dir):
        expected_script_dir = "scripting\\dir"
        get_script_dir.return_value = expected_script_dir

        myscan = TestDefaults()
        with patch("os.listdir") as listdir, \
            patch("os.path.getctime", return_value=1),\
                patch("builtins.open", mock_open(read_data='head1\thead2\thead3\n1\t1\t1\n1\t1\t1\n')) as open:

            listdir.return_value = []
            assert_that(calling(myscan.last_scan),
                        raises(ValueError, "No previous scans in dir (.*)"))



if __name__ == '__main__':
    unittest.main()

