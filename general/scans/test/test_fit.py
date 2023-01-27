import unittest
import numpy as np
from mock import Mock
from parameterized import parameterized
from hamcrest import *

from general.scans.fit import PeakFit, PolyFit, CentreOfMassFit, Fit, ExactFit, TopHat, GaussianFit, \
    DampedOscillatorFit, ErfFit, TopHatFit, SlitScanFit
from general.scans.monoid import ListOfMonoids, Average


class MinimalFit(Fit):
    """
    A fitting class which is used to test the functionality of the Fit metaclass
    """
    def fit(self, x, y, err):
        return None

    def get_y(self, x, fit):
        """
        Evaluate the model described by fit at point x
        """
        return np.polyval(fit, x)

    def readable(self, fit):
        return None


class ScansFitTest(unittest.TestCase):
    """
    Tests for the base Fit class
    """
    # Create a new class which inherits from Fit and call the method on the new class, with the required methods returning None
    def setUp(self):
        self.fitter = MinimalFit(1, "Minimal")

    def test_GIVEN_fit_with_error_WHEN_quality_calculated_THEN_correct_fit_error_returned(self):
        x = np.linspace(0.1, 20.0, 100)
        # measured Y follows 2*x
        real_y = np.polyval([2.0, 0.0], x)

        # Make 'fit' 10% off
        fit = np.poly1d([2.2, 0.0])

        # Fit quality compares measurement errors to fit errors, so make 10% smaller than fit errors
        errs = 0.01 * real_y

        # fit quality is fit error squared
        fit_error = np.sqrt(self.fitter.fit_quality(x, real_y, errs, fit))

        self.assertAlmostEqual(fit_error, 10.0)


class ScansPolyFitTest(unittest.TestCase):
    """
    Tests for the poly fit class
    """
    def setUp(self):
        self.fitter = PolyFit(2)

    def test_GIVEN_sample_polynomial_data_WHEN_fit_performed_THEN_correct_coefficients_returned(self):
        test_polynomial = [-1.0, 0.1, 0.01]

        test_x = np.linspace(-10, 10, 100)
        test_y = np.polyval(test_polynomial, test_x)

        fit = self.fitter.fit(test_x, test_y, 0.1*test_y)

        for fit_coefficient, test_coefficient in zip(fit, test_polynomial):
            self.assertAlmostEqual(fit_coefficient, test_coefficient)

    def test_GIVEN_title_prefix_and_number_WHEN_get_title_THEN_title_contains_prefiz_and_number_are_to_4dp(self):
        params = [2345, 0.12345]
        expected_title_prefix = "title"
        expected_title = "{}: $y = 2.3450e+03x^1 + 0.1235$".format(expected_title_prefix)

        pf = PolyFit(2, expected_title_prefix)
        result = pf.title(params)

        assert_that(result, is_(expected_title))


class ScansPeakFitTest(unittest.TestCase):
    """
    Tests for the peak fitting routines in the scans library
    """

    def setUp(self):
        self.fitter = PeakFit(5)

    def test_GIVEN_data_with_simple_peak_WHEN_peak_fit_performed_THEN_peak_characterised_correctly(self):
        poly_coeffs = [-1, 0.1, 0.01]
        test_function = np.poly1d(poly_coeffs)

        # Obtained by differentiating the quadratic
        test_peak_location = -1.0 * poly_coeffs[1] / (2.0 * poly_coeffs[0])

        test_x = np.linspace(-10, 10, 100)
        test_y = test_function(test_x)

        self.assertAlmostEqual(self.fitter.fit(test_x, test_y, 10.0), test_peak_location, delta=1e-5)

    def test_GIVEN_centre_number_WHEN_get_title_THEN_title_contains_number_are_to_4dp(self):
        params = 0.12345
        expected_title = "Peak at 0.1235"

        pf = PeakFit(100)
        result = pf.title(params)

        assert_that(result, is_(expected_title))

class CentreOfMassFitTest(unittest.TestCase):
    """
    Tests for centre of mass fitting routines
    """

    def setUp(self):
        self.fitter = CentreOfMassFit()

    def test_GIVEN_symmetrical_data_WHEN_fit_performed_THEN_correct_centre_of_mass_returned(self):
        test_x = np.array(np.linspace(0, 20, 100))

        peak_location = 10
        test_function = np.poly1d([-1.0, 0, 10])
        test_y = test_function(test_x - peak_location)

        self.assertAlmostEqual(self.fitter.fit(test_x, test_y, 0.1*test_y)[0], 10.0)

    @parameterized.expand([
        (range(10), range(10), None),
        (range(10), None, range(10)),
        (None, range(10), range(10)),
        ([], range(10), range(10)),
        (range(10), [], range(10)),
        (range(10), range(10), [])
    ])
    def test_GIVEN_invalid_fit_arguments_WHEN_fit_requested_THEN_nan_returned(self, x, y, err):
        fit = self.fitter.fit(x, y, err)
        self.assertEqual(len(fit), 1)
        self.assertIs(fit[0], np.nan)

    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = [0.12345]
        expected_title = "Centre of mass = 0.1235"

        cmf = CentreOfMassFit()
        result = cmf.title(params)

        assert_that(result, is_(expected_title))


class ExactFitTest(unittest.TestCase):
    """
    Tests for the ExactFit class
    """

    def setUp(self):
        self.fitter = ExactFit()

    def test_GIVEN_x_and_y_data_WHEN_readable_form_requested_THEN_data_returned(self):
        x = list(range(1, 10))
        err = x
        y = [2. * value for value in x]

        fit = self.fitter.fit(x, y, err)
        readable_form = self.fitter.readable(fit)
        self.assertListEqual(readable_form['x'], x)
        self.assertListEqual(readable_form['y'], y)


class ErroringFit(Fit):

    def __init__(self, degre, title, expection_to_raise=ValueError):
        super(ErroringFit, self).__init__(degre, title)
        self._expection_to_raise = expection_to_raise

    def fit(self, x, y, err):
        raise self._expection_to_raise("Problems")

    def get_y(self, x, fit):
        raise self._expection_to_raise("Problems")

    def readable(self, fit):
        raise self._expection_to_raise("Problems")


class FitErrorTests(unittest.TestCase):

    def test_GIVEN_fit_errors_WHEN_fit_action_THEN_fit_does_not_throw_exception_but_returns_old_fit(self):
        excepted_old_fit = {"fitparam": 1.0}
        fit = ErroringFit(1, "hi")

        result = fit.fit_plot_action()([1, 2], ListOfMonoids([Average(1,1), Average(2,1)]), None, excepted_old_fit)

        assert_that(result, is_(excepted_old_fit))

    def test_GIVEN_degree_less_than_data_WHEN_fit_action_THEN_fit_returns_none(self):

        degree = 3
        fit = ErroringFit(degree, "hi")

        result = fit.fit_plot_action()([1]*(degree-1), ListOfMonoids([Average(1,1)]*(degree-1)), None, [])

        assert_that(result, is_(None))

    def test_GIVEN_fit_errors_because_of_bad_fit_WHEN_fit_action_THEN_fit_returns_None(self):
        fit = ErroringFit(1, "hi", RuntimeError)

        result = fit.fit_plot_action()([1, 2], ListOfMonoids([Average(1,1), Average(2,1)]), None, [])

        assert_that(result, is_(None))


class TopHatTests(unittest.TestCase):

    def test_GIVEN_data_WHEN_fit_top_hat_THEN_fit_returns_value(self):
        expected_background = 0.1
        expected_height = 2.2
        background = Average(expected_background)
        height = Average(expected_height + expected_background)
        x = [-0.3, -0.2, -0.1, 0, 0.1, 0.2, 0.3]
        y = ListOfMonoids([background, background, height, height, height, background, background])
        fit_action = TopHat.fit_plot_action()

        result = TopHat.readable(fit_action(x, y, Mock(), None))

        assert_that(result, has_entry("center", 0.0))
        assert_that(result, has_entry("background", float(expected_background)))
        assert_that(result, has_entry("height", float(expected_height)))
        assert_that(result, has_entry("width", 0.3))

    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = ([0.12345, 1.2, 2345, 0.01e-4], np.array([[1, 2, 3,0], [4, 5, 6,0], [5,6,7,8], [8,9,10,11]]))

        expected_title = "Top Hat at 0.1235 of width 1.2000"

        thf = TopHatFit()
        result = thf.title(params)

        assert_that(result, is_(expected_title))


class GaussianFitTests(unittest.TestCase):
    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = ([0.12345, 1.2, 2345, 0.01e-4], np.array([[1, 2, 3,0], [4, 5, 6,0], [5,6,7,8], [8,9,10,11]]))

        expected_title = "Gaussian Fit: y=2345*exp((x-0.1235)$^2$/1.2000)+1.0000e-06"

        gf = GaussianFit()
        result = gf.title(params)

        assert_that(result, is_(expected_title))


class DampedOscillatorFitTests(unittest.TestCase):
    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = ([0.12345, 1.2, 2345, 0.01e-4], np.array([[1, 2, 3,0], [4, 5, 6,0], [5,6,7,8], [8,9,10,11]]))

        expected_title = "Damped Oscillator: y=1.2000*exp(-((x-0.1235)/1.0000e-06)$^2$)*cos(2345*(x-0.1235))"

        dof = DampedOscillatorFit()
        result = dof.title(params)

        assert_that(result, is_(expected_title))


class ErfFitTests(unittest.TestCase):
    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = ([0.12345, 1.2, 2345, 0.01e-4], np.array([[1, 2, 3,0], [4, 5, 6,0], [5,6,7,8], [8,9,10,11]]))

        expected_title = "Edge at 0.1235"

        dof = ErfFit()
        result = dof.title(params)

        assert_that(result, is_(expected_title))


class SlitScanFitTests(unittest.TestCase):
    def test_GIVEN_fit_parameters_WHEN_get_title_THEN_numbers_are_to_4dp(self):

        params = ([0.12345, 1.2, 2345], np.array([[1, 2, 3, 0], [4, 5, 6, 0], [5, 6, 7, 8]]))

        expected_title = "Slit Scan Fit: y={1.2000(x-0.1235) E x>0.1235} + 2345"

        ssf = SlitScanFit()
        result = ssf.title(params)

        assert_that(result, is_(expected_title))

    def test_GIVEN_data_WHEN_guess_THEN_background_returned_as_lowest_value(self):
        expected_min = 0.01
        x = np.array([1, 2, 3, 4])
        y = np.array([0.9, 6, expected_min, 1])

        ssf = SlitScanFit()
        result = ssf.guess(x, y)

        assert_that(result[2], is_(expected_min))

    def test_GIVEN_data_WHEN_guess_THEN_center_and_gradient_returned(self):
        expected_background = 0.01
        expected_gradient = 2
        expected_centre = 1

        def val(x):
            return expected_background + 0 if x < expected_centre else expected_gradient * (x - expected_centre)

        x_values = np.array([-1, 0, 1, 2, 3, 4])
        y_values = np.array([val(x_value) for x_value in x_values])

        ssf = SlitScanFit()
        result = ssf.guess(x_values, y_values)

        assert_that(result[0], is_(expected_centre), "centre")
        assert_that(result[1], is_(expected_gradient), "gradient")

    def test_GIVEN_fit_WHEN_get_y_THEN_values_returned(self):
        background = 0.01
        gradient = 2
        centre = 1

        def val(x):
            return background + 0 if x < centre else gradient * (x - centre)

        x_values = np.array([-1, 0, 1, 2, 3, 4])
        expected_value = [float(val(x_value)) for x_value in x_values]

        ssf = SlitScanFit()
        result = ssf.get_y(x_values, [[centre, gradient, background], ])

        for index, (actual, expected) in enumerate(zip(result, expected_value)):
            assert_that(actual, close_to(expected, 1e-6), f"item {index}")
