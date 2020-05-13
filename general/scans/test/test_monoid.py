import unittest
import numpy as np

from mock import MagicMock
from general.scans.monoid import Average, ListOfMonoids


class AverageTest(unittest.TestCase):
    """
    Tests for the averaging class
    """

    def test_GIVEN_count_and_total_as_ints_and_floats_WHEN_err_calculated_THEN_both_answers_are_same(self):
        total = 10.0
        count = 20.0

        int_average = Average(int(total), count=int(count))
        float_average = Average(total, count=count)

        int_err = int_average.err()
        float_err = float_average.err()

        self.assertAlmostEqual(int_err, float_err)

    def test_GIVEN_count_and_total_as_ints_and_floats_WHEN_average_cast_to_string_THEN_both_strings_are_the_same(self):
        total = 10.0
        count = 20.0

        int_average = Average(int(total), count=int(count))
        float_average = Average(total, count=count)

        self.assertEqual(str(int_average), str(float_average))
