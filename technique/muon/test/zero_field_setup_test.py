from technique.muon import zero_field_setup
import unittest
from mock import patch
import numpy as np

AUTO_FEEDBACK_MODE = 1
MANUAL_MODE = 0

class TestZeroFieldSetup(unittest.TestCase):
    def setUp(self):
        self.procedure = zero_field_setup.ZeroFieldSetupProcedure()

    @patch("genie_python.genie.get_pv")
    @patch("technique.muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch('time.sleep', return_value=None)
    def test_GIVEN_all_axis_same_THEN_RMS_value_is_Zero(self, _,
                                                        get_single_field_value_mock, get_pv_mock):
        get_pv_mock.return_value = 1
        get_single_field_value_mock.side_effect = [5] * 60

        value_RMS = self.procedure.calculate_noise(AUTO_FEEDBACK_MODE)

        self.assertEquals(0, value_RMS)


    @patch("technique.muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch("time.sleep", return_value = None)
    def test_GIVEN_all_axis_differnt_value_THEN_RMS_value_is_non_Zero(self, _,
                                                                      get_single_field_value_mock):

        test_val = ([1, 1, 1] * 5) + ([2, 2, 2] * 5) + ([3, 3, 3] * 5) + ([4, 4, 4] * 5)
        get_single_field_value_mock.side_effect = test_val

        test_x = ([1] * 5) + ([2] * 5 )+ ([3] * 5) + ([4] * 5)
        test_y = test_x
        test_z = test_x

        expected = np.sqrt(np.var(test_x) + np.var(test_y) + np.var(test_z))

        actual = self.procedure.calculate_noise(AUTO_FEEDBACK_MODE)
        print(expected)
        self.assertEquals(expected, actual)

    @patch("genie_python.genie.get_pv")
    @patch("technique.muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    @patch("time.sleep", return_value = None)
    @patch("genie_python.genie.set_pv")
    def test_GIVEN_current_and_field_values_THEN_read_current_and_field_values_correctly\
                    (self, set_pv_mock, _, get_single_field_value_mock, get_pv_mock):

        expected_fields = [5] * 21
        expected_currents_x = [-300.0, -280.0, -260.0, -240.0, -220.0, -200.0, -180.0, -160.0, -140.0, -120.0, -100.0,
                               -80.0, -60.0, -40.0, -20.0, 0.0, 20.0, 40.0, 60.0, 80.0, 100.0]
        expected_currents_y = [-100.0, -94.0, -88.0, -82.0, -76.0, -70.0, -64.0, -58.0, -52.0, -46.0, -40.0, -34.0,
                               -28.0, -22.0, -16.0, -10.0, -4.0, 2.0, 8.0, 14.0, 20.0]
        expected_currents_z = [((x - 10) / 10) * 100 for x in range(21)]
        get_single_field_value_mock.return_value = 5
        get_pv_mock.side_effect = [-300.00, -100.00, -100.00, 100, 20, 100]

        actual_values = self.procedure.get_correlated_current_and_fields()

        expected_values = [expected_currents_x, expected_currents_y, expected_currents_z]
        val = [expected_fields] * 3
        expected_values += val
        expected_values = tuple(expected_values)

        self.assertEquals(expected_values, actual_values)


    @patch("technique.muon.zero_field_setup.ZeroFieldSetupProcedure.get_single_corrected_field_value")
    def test_GIVEN_high_output_field_THEN_magnet_not_in_range(self, get_single_field_value_mock):
        get_single_field_value_mock.return_value = 4000
        val = self.procedure.check_magnet_in_range()
        self.assertEquals(val, True)