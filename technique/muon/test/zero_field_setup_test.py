from muon import zero_field_setup
import numpy as np
import unittest
from mock import patch
import random
from scipy import stats


class TestZeroFieldSetup(unittest.TestCase):
    def setUp(self):
        self.procedure = zero_field_setup.ZeroFieldSetupProcedure()
    def tearDown(self):
        pass

    def test_GIVEN_data_THEN_calculate_R_Squared_and_coeffeiceint(self):
        y = [10, 1, 13, 0, 30]
        x = [1, 2, 3, 4, 5]
        coefficient, r_squared = self.procedure.calculate_coefficient_and_r_squared(x, y)

        y = np.array([y])
        expected_coefficient, intercept, r_value, p_value, std_err = stats.linregress(x, y)

        # predicted y values [3, 6.9, 10.8, 14.7, 18.6]
        # actual Residual sum of squares 434.7
        expected_r_squared = r_value ** 2
        
        self.assertEquals([coefficient, r_squared], [expected_coefficient, expected_r_squared])

    @patch("genie_python.genie.get_pv")
    @patch("muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch('time.sleep', return_value=None)
    def test_GIVEN_all_axis_same_THEN_RMS_value_is_Zero(self, time_sleep,  get_single_field_value_mock, get_pv_mock):
        get_pv_mock.return_value = 1
        get_single_field_value_mock.side_effect = [5] * 60

        value_RMS = self.procedure.calculate_noise()

        self.assertEquals(0, value_RMS)


    @patch("muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch("time.sleep", return_value = None)
    def test_GIVEN_all_axis_differnt_value_THEN_RMS_value_is_non_Zero(self, patched_time_sleep,
                                                                      get_single_field_value_mock):

        get_single_field_value_mock.side_effect = [round(5-random.uniform(0.5, 1.5), 1) for x in range(60)]
        value_RMS = self.procedure.calculate_noise()

        self.assertLess(value_RMS, 5)

    @patch("genie_python.genie.get_pv")
    @patch("muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch("time.sleep", return_value = None)
    def test_GIVEN_current_and_field_values_THEN_read_current_and_field_values_correctly\
                    (self, patched_time_sleep, get_single_field_value_mock, get_pv_mock):

        expected_fields = [5 for x in range(21)]
        expected_currents = [(((x - 10) / 10.0) * 100) for x in range(21)]

        get_single_field_value_mock.return_value = 5
        get_pv_mock.return_value = 100.00

        actual_values = self.procedure.get_correlated_current_and_fields()

        expected_values = [expected_currents] * 3
        val = [expected_fields] * 3
        expected_values += val
        expected_values = tuple(expected_values)
        self.assertEquals(expected_values, actual_values)


    @patch("muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    def test_GIVEN_high_output_field_THEN_magnet_not_in_range(self, get_single_field_value_mock):
        get_single_field_value_mock.return_value = 4000
        val = self.procedure.check_if_stray_field_exist()
        self.assertEquals(val, True)