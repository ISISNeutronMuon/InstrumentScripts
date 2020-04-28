import math
import unittest

from hamcrest import *

from general.scans.monoid import Average


class TestMoniods(unittest.TestCase):

    def test_GIVEN_average_WHEN_zero_total_and_count_is_zero_THEN_float_is_zero(self):

        av = Average(0, 0)

        result = float(av)

        assert_that(result, is_(0.0))

    def test_GIVEN_average_WHEN_zero_total_and_count_is_zero_THEN_error_is_zero(self):
        av = Average(0, 0)

        result = av.err()

        assert_that(result, is_(0.0))

    def test_GIVEN_average_WHEN_non_zero_total_and_count_is_zero_THEN_float_is_nan(self):
        av = Average(1, 0)

        result = float(av)

        assert_that(math.isnan(result), is_(True), "Is nan")

    def test_GIVEN_average_WHEN_non_zero_total_and_count_is_zero_THEN_error_is_nan(self):
        av = Average(1, 0)

        result = av.err()

        assert_that(math.isnan(result), is_(True), "Is nan")


if __name__ == '__main__':
    unittest.main()
