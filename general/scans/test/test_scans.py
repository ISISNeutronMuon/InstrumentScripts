import unittest

from ..scans import SimpleScan, ReplayScan


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
