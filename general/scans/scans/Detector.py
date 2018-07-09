"""This module adds a helper class for detectors."""
from functools import wraps
try:
    # pylint: disable=import-error
    from genie_python import genie as g
except ImportError:
    from .Mocks import g


class DetectorManager(object):
    """Manage routines for pulling data from the instrument"""
    def __init__(self, f):
        self._f = f
        self.scan = None

    def __call__(self, scan, **kwargs):
        self.scan = scan
        return self

    def __enter__(self):
        if g.get_runstate() != "SETUP":  # pragma: no cover
            raise RuntimeError("Cannot start scan while already in a run!" +
                               " Current state is: " + str(g.get_runstate()))
        return self._f

    def __exit__(self, typ, value, traceback):
        pass


class DaePeriods(DetectorManager):
    """This helper class aids in making detector managers that perform all
    of their measurements in a single DAE run, instead of constantly
    starting and stoping the DAE."""

    def __init__(self, f, pre_init, period_function=len):
        """Create a new detector manager that runs in a single Dae run

        Parameters
        ----------
        f: Function
          The actual detector command.  Should return a Monoid with the
          measured value.
        pre_init: Function
          Any additional setup that's needed by the detector (e.g. starting
          wiring tables)
        period_function: Function
          A function that takes a scan and calculates the number of periods
          that need to be created.  The default value is to just take the
          length of the scan.
        """
        self._pre_init = pre_init
        self._save = True  # Default value should never be reachable
        self.period_function = period_function
        self._scan = None
        self._kwargs = {}
        DetectorManager.__init__(self, f)

    def __call__(self, scan, save, **kwargs):
        self._pre_init()
        self._save = save
        self._kwargs = kwargs
        self._scan = scan
        return self

    def __enter__(self):
        if g.get_runstate() != "SETUP":  # pragma: no cover
            raise RuntimeError("Cannot start scan while already in a run!" +
                               " Current state is: " + str(g.get_runstate()))
        kwargs = self._kwargs
        if "title" in kwargs:
            title = kwargs["title"]
        else:
            title = "Scan"
        g.change_title(title)
        g.change(nperiods=self.period_function(self._scan))
        g.begin(paused=1)

        @wraps(self._f)
        def wrap(*args, **kwargs):
            """Wrapped function to change periods"""
            x = self._f(*args, **kwargs)
            g.change_period(1+g.get_period())
            return x

        return wrap

    def __exit__(self, typ, value, traceback):
        if self._save:
            g.end()
        else:
            g.abort()


def dae_periods(pre_init=lambda: None, period_function=len):
    """Decorate to add single run number support to a detector function"""
    def inner(func):
        """wrapper"""
        return DaePeriods(func, pre_init, period_function=period_function)
    return inner
