import unittest

from ..scans import SimpleScan


class SimpleScanTests(unittest.TestCase):
    """
    Tests for the SimpleScan class
    """

    def test_GIVEN_map_function_WHEN_map_applied_THEN_new_class_has_mapped_values_in_container(self):
        initial_values = [1., 2., 3.]

        def map_function(x):
            return 2.0 * x

        simple_scan = SimpleScan('action', initial_values, 'defaults')

        mapped_simple_scan = simple_scan.map(map_function)

        self.assertFalse(isinstance(mapped_simple_scan.values, map))

        for initial_value, mapped_value in zip(initial_values, mapped_simple_scan.values):
            self.assertEqual(map_function(initial_value), mapped_value)
