import numpy as np
import unittest
from contextlib import contextmanager

from general.scans.plot_functions import PlotFunctions, NO_POINTS_MAX_Y, NO_POINTS_MIN_Y, INF_POINT_MIN_Y, \
    INF_POINT_MAX_Y, DEFAULT_FRACTION_SPACING_TO_ADD
from general.scans.scans import SimpleScan, ReplayScan
from hamcrest import *
from mock import Mock, patch

from general.scans.defaults import Defaults
from general.scans.monoid import Average, MonoidList, ListOfMonoids, Exact
from general.scans.motion import Motion
from parameterized import parameterized


class PlotFunctionsTests(unittest.TestCase):
    """
    Tests for the Scan classes
    """

    def setUp(self) -> None:
        self.figure_mock = Mock()
        self.axis_mock = Mock()
        self.plot_functions = PlotFunctions()
        self.plot_functions.set_figure_and_axis(self.figure_mock, self.axis_mock)

    def test_GIVEN_points_are_none_WHEN_plot_data_with_errors_THEN_range_set_to_correct_defaults(self):

        self.plot_functions.plot_data_with_errors([], None)

        self.axis_mock.set_ylim.assert_called_with(NO_POINTS_MIN_Y, NO_POINTS_MAX_Y)

    @parameterized.expand([([], NO_POINTS_MIN_Y, NO_POINTS_MAX_Y),
                           ([np.Inf], INF_POINT_MIN_Y, INF_POINT_MAX_Y),
                           ([1, np.PINF], 1-INF_POINT_MAX_Y*DEFAULT_FRACTION_SPACING_TO_ADD, 1+INF_POINT_MAX_Y* (1 + DEFAULT_FRACTION_SPACING_TO_ADD)),
                           ([1, np.NINF], 1-INF_POINT_MAX_Y*(1 + DEFAULT_FRACTION_SPACING_TO_ADD), 1+INF_POINT_MAX_Y*DEFAULT_FRACTION_SPACING_TO_ADD),
                           ([10, -10], -10-20*DEFAULT_FRACTION_SPACING_TO_ADD, 10+20*DEFAULT_FRACTION_SPACING_TO_ADD)])
    def test_GIVEN_points_WHEN_plot_data_with_errors_THEN_range_set_to_correct(self, values, expected_miny, expected_maxy):
        values_as_monoid_list = ListOfMonoids([Exact(val) for val in values])

        self.plot_functions.plot_data_with_errors([], values_as_monoid_list)

        miny, maxy = self.axis_mock.set_ylim.call_args[0]
        assert_that(miny, is_(close_to(expected_miny, 1e-3)))
        assert_that(maxy, is_(close_to(expected_maxy, 1e-3)))

    def test_GIVEN_points_WHEN_plot_data_with_errors_THEN_data_is_plotted(self):
        expected_data = [Average(val) for val in [1.0, 2.0, 3.0]]
        values_as_monoid_list = ListOfMonoids(expected_data)

        self.plot_functions.plot_data_with_errors([2.0, 3.0, 5.0], values_as_monoid_list)

        self.axis_mock.errorbar.assert_called()

    def test_GIVEN_list_of_point_WHEN_plot_data_with_errors_THEN_data_is_plotted_for_all_points(self):
        expected_count = 3
        expected_data = MonoidList([Average(val) for val in [1.0, 2.0, 3.0]])
        values_as_list_of_monoid_list = ListOfMonoids(MonoidList([expected_data] * expected_count))

        self.plot_functions.plot_data_with_errors([2.0, 3.0, 5.0], values_as_list_of_monoid_list)

        assert_that(self.axis_mock.errorbar.call_count, is_(expected_count), "Should be called once for each set of numbers")

    def test_GIVEN_points_WHEN_plot_data_with_errors_THEN_plot_is_styled_correctly(self):
        expected_marker = "f"
        expected_size = 2764
        expected_colour = "mycol"
        self.plot_functions.data_markers = [expected_marker]
        self.plot_functions.data_marker_size = expected_size
        self.plot_functions.color_cycle = [expected_colour]
        expected_data = [Average(val) for val in [1.0, 2.0, 3.0]]
        values_as_monoid_list = ListOfMonoids(expected_data)

        self.plot_functions.plot_data_with_errors([2.0, 3.0, 5.0], values_as_monoid_list)

        settings = self.axis_mock.errorbar.call_args[1]
        assert_that(settings, has_entry("color", expected_colour))
        assert_that(settings, has_entry("markersize", expected_size))
        assert_that(settings, has_entry("marker", expected_marker))

    def test_GIVEN_x_min_and_max_WHEN_setup_plot_THEN_axes_are_cleared_and_x_range_set(self):

        self.plot_functions.setup_plot(1, 3)
        expected_minx = 1 - (3 - 1) * DEFAULT_FRACTION_SPACING_TO_ADD
        expected_maxx = 3 + (3 - 1) * DEFAULT_FRACTION_SPACING_TO_ADD

        self.axis_mock.clear.assert_called()
        minx, maxx = self.axis_mock.set_xlim.call_args[0]
        assert_that(minx, is_(close_to(expected_minx, 1e-3)))
        assert_that(maxx, is_(close_to(expected_maxx, 1e-3)))

    @parameterized.expand([("lab", None, "lab"),
                           ("lab", "unit", "lab (unit)"),
                           (None, "unit", "unit")])
    @patch("general.scans.plot_functions.plt")
    def test_GIVEN_x_label_WHEN_setup_plot_THEN_axes_and_title_set_correction(self, label, unit, expected, plt_mock):
        manager_mock = Mock()
        plt_mock.get_current_fig_manager.return_value = manager_mock
        figure = 1
        self.figure_mock.number = figure
        expected_title = "Figure {}: {}".format(figure, expected)
        self.plot_functions.setup_plot(1, 3, x_label=label, x_unit=unit)

        self.axis_mock.set_xlabel.assert_called_with(expected)
        manager_mock.set_window_title.assert_called_with(expected_title)

    @parameterized.expand([("lab", None, "lab"),
                           ("lab", "unit", "lab (unit)"),
                           (None, "unit", "unit")])
    def test_GIVEN_y_label_WHEN_setup_plot_THEN_axes_set_correction(self, label, unit, expected):
        self.plot_functions.setup_plot(1, 3, y_label=label, y_unit=unit)

        self.axis_mock.set_ylabel.assert_called_with(expected)

    def test_GIVEN_save_name_WHEN_saved_THEN_figure_is_saved(self):
        expected_name = "name"
        self.plot_functions.save(expected_name)

        self.figure_mock.savefig.assert_called_with(expected_name)

    def test_GIVEN_no_save_name_WHEN_saved_THEN_figure_is_not_saved(self):
        self.plot_functions.save(None)

        self.figure_mock.savefig.assert_not_called()

    def test_GIVEN_fit_data_WHEN_plot_fit_THEN_fit_plotted_with_correct_colour(self):
        expected_colour = "mycol"
        self.plot_functions.fit_colour = expected_colour
        self.plot_functions.plot_fit([], np.array([1,2,2]), "myfit")

        settings = self.axis_mock.plot.call_args[1]
        assert_that(settings, has_entry("color", expected_colour))

    def test_GIVEN_line_pos_WHEN_plot_line_THEN_fit_plotted_with_correct_colour(self):
        expected_colour = "mycol"
        self.plot_functions.fit_colour = expected_colour
        self.plot_functions.plot_vertical_fit_line(3.7, "myfit")

        settings = self.axis_mock.axvline.call_args[1]
        assert_that(settings, has_entry("color", expected_colour))


if __name__ == '__main__':
    unittest.main()

