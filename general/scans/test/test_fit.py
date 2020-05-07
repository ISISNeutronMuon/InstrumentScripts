import unittest
from mock import Mock
import numpy as np

from ..fit import PeakFit


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
