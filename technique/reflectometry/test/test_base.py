import unittest
from collections import OrderedDict
from contextlib import contextmanager

import mock
from mock import Mock, patch
from parameterized import parameterized
from genie_python import genie as g

from ..base import reset_hgaps_and_sample_height, auto_height


class ReflBaseTest(unittest.TestCase):
    """
    Tests
    """
    def test_GIVEN_reset_hgaps_WHEN_noop_THEN_hgaps_reset(self):
        movement = Mock()

        movement.set_h_gaps = Mock()

        expected_ordered_dict = OrderedDict([("S1HG", 10.0),
                                             ("S2HG", 20.0),
                                             ("S3HG", 30.0),
                                             ("S4HG", 40.0)])

        movement.get_gaps = Mock(return_value=expected_ordered_dict)

        sample = Mock()
        constant = Mock()
        @reset_hgaps_and_sample_height(movement, sample, constant)
        def noop_function():
            pass

        noop_function()
        movement.set_h_gaps.assert_called_with(**expected_ordered_dict)


@contextmanager
def genie_python_sim(block_inits=None, blocks_in_alarm=None):
    """
    Context which creates a fake block server by mocking out parts of genie

    Parameters
    ----------
    block_and_value: blocks and their initial values

    Returns
    -------
    nothing
    """
    blocks = {}
    if block_inits is None:
        block_inits = {}
    if blocks_in_alarm is None:
        blocks_in_alarm = []
    with patch("genie_python.genie.cget") as cget, \
            patch("genie_python.genie.cset") as cset, \
            patch("genie_python.genie.check_alarms") as check_alarms, \
            patch("genie_python.genie.waitfor_move") as waitfor_move:

        def mock_cget(pv):
            try:
                return {"value": blocks[pv]}
            except KeyError:
                return None

        def mock_cset(pv, value):
            try:
                blocks[pv] = value
            except KeyError:
                print("Block did not exist {}".format(pv))

        def mock_check_alarms(*blocks_to_check):
            blocks_to_check = list(blocks_to_check)
            return [block for block in blocks_to_check if block in blocks_in_alarm]

        def mock_waitfor_move(*args, **kwargs):
            pass

        cget.side_effect = mock_cget
        cset.side_effect = mock_cset
        check_alarms.side_effect = mock_check_alarms
        waitfor_move.side_effect = mock_waitfor_move

        for block, value in block_inits.items():
            cset(block, value)

        yield


class ReflAutoHeightTest(unittest.TestCase):
    """
    Tests
    """
    laser_block = "laser"
    height_block = "height"

    @parameterized.expand([(1, 0, -1),
                           (-1, 0, 1),
                           (-1, -1, 0),
                           (1, 1, 0),
                           (2, 10, 8),
                           (10, 2, -8)])
    def test_GIVEN_laser_offset_WHEN_setting_auto_height_THEN_height_moves_by_difference(self, initial_laser_offset, initial_height, expected):
        with genie_python_sim({self.laser_block: initial_laser_offset, self.height_block: initial_height}):

            auto_height(self.laser_block, self.height_block)
            actual = g.cget(self.height_block)["value"]

            self.assertEqual(expected, actual)

    @parameterized.expand([(0, 2, 2),
                           (0, -2, -2),
                           (1, 2, 1),
                           (1, -2, -3),
                           (-1, 2, 3),
                           (-1, -2, -1)])
    def test_GIVEN_laser_offset_and_non_default_target_WHEN_setting_auto_height_THEN_height_moves_by_difference_between_laser_and_target(self, initial_laser_offset, target, expected_height):
        initial_height = 0
        with genie_python_sim({self.laser_block: initial_laser_offset, self.height_block: initial_height}):

            auto_height(self.laser_block, self.height_block, target=target)
            actual_height = g.cget(self.height_block)["value"]

            self.assertEqual(expected_height, actual_height)

    def test_GIVEN_height_block_in_alarm_WHEN_setting_auto_height_THEN_alert_with_prompt(self):
        with genie_python_sim({self.laser_block: 0, self.height_block: 0}, blocks_in_alarm=[self.height_block]), \
             patch('general.utilities.io.alert_on_error') as alert_on_error:

            auto_height(self.laser_block, self.height_block)

            alert_on_error.assert_called_with(mock.ANY, True)

    def test_GIVEN_laser_block_value_invalid_and_continue_is_false_WHEN_setting_auto_height_THEN_alert_with_prompt(self):
        nonsense_val = "nonsense"
        expected_prompt = True
        with genie_python_sim({self.laser_block: nonsense_val, self.height_block: 0}), \
             patch('general.utilities.io.alert_on_error') as alert_on_error:

            auto_height(self.laser_block, self.height_block, continue_if_nan=False)

            alert_on_error.assert_called_with(mock.ANY, expected_prompt)

    def test_GIVEN_laser_block_value_invalid_and_continue_is_true_WHEN_setting_auto_height_THEN_alert_without_prompt(self):
        nonsense_val = "nonsense"
        expected_prompt = False
        with genie_python_sim({self.laser_block: nonsense_val, self.height_block: 0}), \
             patch('general.utilities.io.alert_on_error') as alert_on_error:

            auto_height(self.laser_block, self.height_block, continue_if_nan=True)

            alert_on_error.assert_called_with(mock.ANY, expected_prompt)

    def test_GIVEN_blocks_not_in_alarm_and_no_nonsensical_values_WHEN_setting_auto_height_THEN_completed_without_alert(self):
        with genie_python_sim({self.laser_block: 0, self.height_block: 0}), \
             patch('general.utilities.io.alert_on_error') as alert_on_error:

            auto_height(self.laser_block, self.height_block)

            alert_on_error.assert_not_called()
