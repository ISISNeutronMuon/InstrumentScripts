"""
Utilities to  run user buttons

See
"""

import traceback
from concurrent.futures.thread import ThreadPoolExecutor
from time import sleep

from genie_python import genie as g
from genie_python.genie_cachannel_wrapper import CaChannelWrapper, UnableToConnectToPVException

# PV template for the button
BUTTON_PV_TEMPLATE = "PARS:USER:BUTTON{}"

# Defined buttons
_buttons = {}


class _ButtonMonitor:
    """
    Run the general button logic
    """
    def __init__(self, button_index, name, function, block_until_pv_exists, retry_delay):
        """
        Construct a new button.

        Parameters
        ----------
        button_index(int): index of button
        name(str): name of the action
        function: function to run when button is pressed. Should have one argument which is a function which sets the
            status with a string, e.g. func(set_status):  set_state("Starting")
        block_until_pv_exists: True wait for the block to exist; False throw an exception if the button pv doesn't exist
        retry_delay: If blocking until the pv exists then retry every this number of seconds
        """
        print("Creating button {}".format(name))
        self._button_index = button_index
        self._function = function

        self._pv = g.prefix_pv_name(BUTTON_PV_TEMPLATE.format(button_index))
        self._executor = ThreadPoolExecutor(max_workers=1)

        while True:
            try:
                CaChannelWrapper.set_pv_value(self._pv, "")
                CaChannelWrapper.set_pv_value("{}:SP".format(self._pv), "")
                CaChannelWrapper.set_pv_value("{}:SP.DESC".format(self._pv), name)
                self._clear_monitor = CaChannelWrapper.add_monitor("{}:SP".format(self._pv), self._button_function)
                break
            except UnableToConnectToPVException:
                if not block_until_pv_exists:
                    break
            sleep(retry_delay)

    def _button_function(self, value, _, __):
        """
        If the button is running then run the user function in a thread
        Parameters
        ----------
        value: value of the button set point
        """
        if value == "Running":
            self._executor.submit(self._executed_function)

    def _set_status(self, value):
        """
        Set the status pv string to a value
        Parameters
        ----------
        value (str): value to set
        """
        print(self._pv)
        CaChannelWrapper.set_pv_value(self._pv, value)

    def _executed_function(self):
        """
        Executes the users function. After the function has run set the set point back to blank.
        """
        try:
            self._function(self._set_status)
        except Exception:
            self._set_status("Error")
            traceback.print_exc()
            raise
        finally:
            CaChannelWrapper.set_pv_value("{}:SP".format(self._pv), "")

    def clean_up(self):
        """
        clean_up resources
        """
        self._clear_monitor()
        self._executor.shutdown()


def add_button_function(button_index, name, function, block_until_pv_exists=True, retry_delay=5):
    """
    Add a function to a given button so it will execute when the button is pressed.

    Parameters
    ----------
    button_index: index of the button (0 to NUM_USER_BUTTONS)
    name: name of the action that function performs
    function: function to run when button is clicked. Should have one argument which is a function which can be used to
            set the button status with a string, e.g. def my_func(set_status):  set_state("Starting")
    block_until_pv_exists: Wait to connect to button until it exists; False throw exception
    retry_delay: delay between retries if blocking

    Returns
    -------
    The button
    """
    try:
        _buttons[button_index].clean_up()
    except KeyError:
        # button hasn't been previously defined
        pass
    button = _ButtonMonitor(button_index, name, function, block_until_pv_exists, retry_delay)
    _buttons[button_index] = button
    return button


def run_buttons():
    """
    Loop which runs the code for the given buttons, and cleans up after the loop ends.
    """
    try:
        while True:
            sleep(10)
    finally:
        print("clean up")
        for button in _buttons.values():
            button.clean_up()
