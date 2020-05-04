import unittest
from collections import OrderedDict
from mock import Mock

from ..base import reset_hgaps_and_sample_height


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
