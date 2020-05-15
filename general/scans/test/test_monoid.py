import unittest

from parameterized import parameterized

from general.scans.monoid import Average, Sum

class SumTest(unittest.TestCase):
    """
    Tests for the Sum class
    """

    @parameterized.expand([
        (0, 1)
    ])
    def test_GIVEN_sum_with_value_zero_WHEN_number_added_THEN_sum_is_correct(self, init_value, added_value):
        summer = Sum(0)
        new_sum = summer + 1
        self.assertEqual(new_sum.total, init_value + added_value)


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
