import unittest
from time import sleep

from genie_python.channel_access_exceptions import UnableToConnectToPVException
from mock import Mock, patch

from hamcrest import *

from general.utilities import button_functions
from general.utilities.button_functions import add_button_function, BUTTON_PV_TEMPLATE
from CaChannel._ca import AlarmSeverity, AlarmCondition

class OnPVChangeTests(unittest.TestCase):
    """
    Tests for the Scan classes
    """

    def setUp(self) -> None:
        button_functions._buttons = {}

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_WHEN_add_button_THEN_monitor_setup(self, ca_channel_wrapper, mock_genie):
        prefix = "prefix"

        base_pv = "expected_pv"
        mock_genie.prefix_pv_name.return_value = base_pv
        mock_function = Mock()
        button_index = 0

        add_button_function(button_index, "name", mock_function)

        mock_genie.prefix_pv_name.assert_called_with(BUTTON_PV_TEMPLATE.format(button_index))
        pv = ca_channel_wrapper.add_monitor.call_args[0][0]
        assert_that(pv, is_("{}:SP".format(base_pv)))

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_WHEN_pv_set_to_running_THEN_function_is_called(self, ca_channel_wrapper, mock_genie):
        mock_function = Mock()
        add_button_function(0, "name", mock_function)
        function_to_call_on_monitor = ca_channel_wrapper.add_monitor.call_args[0][1]

        function_to_call_on_monitor("Running", AlarmSeverity.No, AlarmCondition.No)

        sleep(0.1)  # wait for function to execute on other thread

        mock_function.assert_called()

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_WHEN_pv_not_set_to_running_THEN_function_is_not_called(self, ca_channel_wrapper, mock_genie):
        mock_function = Mock()
        add_button_function(0, "name", mock_function)
        function_to_call_on_monitor = ca_channel_wrapper.add_monitor.call_args[0][1]

        function_to_call_on_monitor("", AlarmSeverity.No, AlarmCondition.No)

        sleep(0.1)  # wait for function to execute on other thread

        mock_function.assert_not_called()

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_WHEN_add_button_THEN_description_is_set_and_function_is_set_as_not_running_and_status_is_blanked(self, ca_channel_wrapper, mock_genie):

        base_pv = "pv"
        mock_genie.prefix_pv_name.return_value = base_pv
        mock_function = Mock()
        button_index = 1

        expected_description = "name"
        add_button_function(button_index, expected_description, mock_function)

        ca_channel_wrapper.set_pv_value.assert_any_call("{}:SP.DESC".format(base_pv), expected_description)
        ca_channel_wrapper.set_pv_value.assert_any_call("{}:SP".format(base_pv), "")
        ca_channel_wrapper.set_pv_value.assert_any_call(base_pv, "")

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_add_button_with_block_until_available_WHEN_not_available_and_then_available_THEN_monitor_setup(self, ca_channel_wrapper, mock_genie):
        prefix = "prefix"

        expected_pv = "expected_pv"
        mock_genie.prefix_pv_name.return_value = expected_pv
        ca_channel_wrapper.add_monitor.side_effect = [UnableToConnectToPVException("", ""), None]
        mock_function = Mock()
        button_index = 0

        add_button_function(button_index, "name", mock_function, retry_delay=0.1)

        assert_that(ca_channel_wrapper.add_monitor.call_count, is_(2), "add_monitor called twice, after first cal fails")

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_WHEN_pv_set_to_running_and_function_throws_THEN_button__is_set_back_to_not_running(self, ca_channel_wrapper, mock_genie):
        base_pv = "pv"
        mock_genie.prefix_pv_name.return_value = base_pv
        mock_function = Mock(side_effect=ValueError())
        add_button_function(0, "name", mock_function)
        function_to_call_on_monitor = ca_channel_wrapper.add_monitor.call_args[0][1]

        function_to_call_on_monitor("Running", AlarmSeverity.No, AlarmCondition.No)

        sleep(0.1)  # wait for function to execute on other thread

        ca_channel_wrapper.set_pv_value.assert_any_call("{}:SP".format(base_pv), "")

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_button_WHEN_finish_THEN_monitor_is_cleared(self, ca_channel_wrapper, mock_genie):
        clear_func = Mock()
        ca_channel_wrapper.add_monitor.return_value = clear_func
        button = add_button_function(0, "name", Mock())

        button.clean_up()

        clear_func.assert_called()

    @patch("general.utilities.button_functions.g")
    @patch("general.utilities.button_functions.CaChannelWrapper")
    def test_GIVEN_function_sets_status_pv_WHEN_pv_set_to_running_THEN_status_is_set(self, ca_channel_wrapper, mock_genie):
        expected_status = "status"
        base_pv = "pv"
        mock_genie.prefix_pv_name.return_value = base_pv

        def my_function(set_status):
            set_status(expected_status)
        add_button_function(0, "name", my_function)
        function_to_call_on_monitor = ca_channel_wrapper.add_monitor.call_args[0][1]

        function_to_call_on_monitor("Running", AlarmSeverity.No, AlarmCondition.No)

        sleep(0.1)  # wait for function to execute on other thread

        ca_channel_wrapper.set_pv_value.assert_any_call(base_pv, expected_status)


if __name__ == '__main__':
    unittest.main()
