import unittest
import numpy as np
from parameterized import parameterized

from ..fit import PeakFit, PolyFit, CentreOfMassFit, Fit


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
    # Create a new class which inherits off Fit and call the method on the new class, with the required methods returning None
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
        self.assertEquals(len(fit), 1)
        self.assertIs(fit[0], np.nan)
