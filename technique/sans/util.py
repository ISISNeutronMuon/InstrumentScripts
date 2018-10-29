"""Useful utilities for scriping"""
from functools import wraps
import logging
from logging import info
from .genie import SwitchGenie


def dae_setter(suffix, measurement_type):
    """Declare that a method sets the DAE wiring table

    Parameters
    ==========
    suffix : str
      The footer to be put on all run titles in this mode
    measurement_type : str
      The default measurement_type to be recorded in the journal

    Returns
    =======
    A decorator for setting the dae mode

    This decorator was designed to work on subclasses of the
    :py:class:`src.Instrument.ScanningInstrument` class.  The
    following functionality is added into the class

    1. If the wiring tables are already in the correct state, the function
       returns immediately without taking any other actions
    2. If the wiring tables are in a different state, the change to the wiring
       tables is printed to the prompt before performing the actual change


    #1 of the above is the most important, as it allows the wiring
    tables to be set on any function call without worrying about
    wasting time reloading an existing configuration

    Please note that this decorator assumes that the title of the
    method begins with "setup_dae", followed by the new of the state
    of the wiring table.

    """
    def decorator(inner):
        """The actual decorator with the given parameters"""
        @wraps(inner)
        def wrapper(self, *args, **kwargs):
            """Memoize the dae mode"""
            request = inner.__name__[10:]
            if request == self._dae_mode:  # pylint: disable=protected-access
                debug("instrument was already set for {}".format(request)
                return
            inner(self, *args, **kwargs)
            info("Setup {} for {}".format(type(self).__name__,
                                          request.replace("_", " ")))
            self._dae_mode = request  # pylint: disable=protected-access
            self.title_footer = "_" + suffix
            self.measurement_type = measurement_type
        return wrapper
    return decorator


SCALES = {"uamps": 90, "frames": 0.1, "seconds": 1,
          "minutes": 60, "hours": 3600}


def wait_time(call):
    """
    Calculate the time spent waiting by a mock wait call.

    Parameters
    ----------
    call : mock.Call
      A mock call that might be a waitfor command
    Returns
    -------
    float
      The approximate time in seconds needed for this command.
    """
    name, _, kwargs = call
    if name != "waitfor":
        return 0
    key = list(kwargs.keys())[0]
    return SCALES[key] * kwargs[key]


def pretty_print_time(seconds):
    """
    Given a number of seconds, generate a human readable time string.

    Parameters
    ----------
    seconds : float
      The time in seconds that the script will require.
    Returns
    -------
    str
      A string giving the time needed in hours and an approximate ETA.
    """
    from datetime import timedelta, datetime
    hours = seconds/3600.0
    delta = timedelta(0, seconds)
    skeleton = "The script should finish in {} hours\nat {}"
    return skeleton.format(hours, delta+datetime.now())


def user_script(script):
    """A decorator to perform some sanity checking on a user script before
    it is run"""
    @wraps(script)
    def inner(*args, **kwargs):
        """Mock run a script before running it for real."""
        from mock import Mock
        from .genie import mock_gen
        code = script.__name__ + "("
        code += ", ".join(map(str, args))
        for k in kwargs:
            code += ", " + k + "=" + str(kwargs[k])
        code += ")"
        mock_gen.reset_mock()
        logging.getLogger().disabled = True
        try:
            old = SwitchGenie.MOCKING_MODE
            SwitchGenie.MOCKING_MODE = True
            eval(code,  # pylint: disable=eval-used
                 {"MOCKING_MODE": True, "logging": Mock()},
                 {script.__name__: script})
            SwitchGenie.MOCKING_MODE = old
        finally:
            logging.getLogger().disabled = False
        calls = mock_gen.mock_calls
        time = sum([wait_time(call) for call in calls])
        logging.info(pretty_print_time(time))
        script(*args, **kwargs)
    return inner
