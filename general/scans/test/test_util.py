import unittest

from general.scans.util import get_points
from hamcrest import *


class UtilTests(unittest.TestCase):
    """
    Tests for the Scan classes
    """

    def test_GIVEN_start_stop_and_stride_exact_WHEN_get_points_THEN_first_last_and_each_stide_point_returned(self):

        result = get_points(current=0, start=1.0, stop=4.0, stride=1)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0, 4.0))

    def test_GIVEN_start_stop_and_stride_inexact_WHEN_get_points_THEN_start_end_and_approximate_stride_returned(self):

        result = get_points(current=0, start=1.0, stop=3.7, stride=1.0)

        assert_that(result, contains_exactly(1.0, 1.9, 2.8, 3.7))

    def test_GIVEN_start_stop_and_stride_inexact_and_stride_backwards_WHEN_get_points_THEN_start_end_and_approximate_stride_returned(self):

        result = get_points(current=0, start=-1.0, stop=-3.7, stride=-1.0)

        assert_that(result, contains_exactly(-1.0, -1.9, -2.8, -3.7))

    def test_GIVEN_start_stop_and_count_WHEN_get_points_THEN_first_last_and_two_in_middle(self):

        result = get_points(current=0, start=1.0, stop=4.0, count=4)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0, 4.0))

    def test_GIVEN_start_stop_and_step_exact_WHEN_get_points_THEN_first_and_each_step_point_returned_but_not_last(self):

        result = get_points(current=0, start=1, stop=4, step=1)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0))

    def test_GIVEN_start_stop_and_step_inexact_WHEN_get_points_THEN_start_and_each_step_but_not_end_point_are_included(self):

        result = get_points(current=0, start=1.0, stop=3.7, step=1.0)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0))

    def test_GIVEN_start_step_and_count_WHEN_get_points_THEN_first_last_and_each_step_point_returned(self):

        result = get_points(current=0, start=1.0, count=4, step=1.0)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0, 4.0))

    def test_GIVEN_start_stride_and_count_WHEN_get_points_THEN_first_last_and_each_step_point_returned(self):

        result = get_points(current=0, start=1.0, count=4, stride=1.0)

        assert_that(result, contains_exactly(1.0, 2.0, 3.0, 4.0))

if __name__ == '__main__':
    unittest.main()

